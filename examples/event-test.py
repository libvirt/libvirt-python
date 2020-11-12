#!/usr/bin/env python3
#
#
#
##############################################################################
# Start off by implementing a general purpose event loop for anyone's use
##############################################################################

import atexit
import os
import libvirt
import select
import errno
import time
import threading
from argparse import ArgumentParser
from typing import Any, Callable, Dict, List, Optional, TypeVar  # noqa F401
_T = TypeVar("_T")
_EventCallback = Callable[[int, int, int, _T], None]
_TimerCallback = Callable[[int, _T], None]


# This example can use three different event loop impls. It defaults
# to a portable pure-python impl based on poll that is implemented
# in this file.
#
# When Python >= 3.4, it can optionally use an impl based on the
# new asyncio module.
#
# Finally, it can also use the libvirt native event loop impl
#
# This setting thus allows 'poll', 'native' or 'asyncio' as valid
# choices
#
event_impl = "poll"

do_debug = False


def debug(msg: str) -> None:
    if do_debug:
        print(msg)


#
# This general purpose event loop will support waiting for file handle
# I/O and errors events, as well as scheduling repeatable timers with
# a fixed interval.
#
# It is a pure python implementation based around the poll() API
#
class virEventLoopPoll:
    # This class contains the data we need to track for a
    # single file handle
    class virEventLoopPollHandle:
        def __init__(self, handle: int, fd: int, events: int, cb: _EventCallback, opaque: _T):
            self.handle = handle
            self.fd = fd
            self.events = events
            self.cb = cb
            self.opaque = opaque

        def get_id(self) -> int:
            return self.handle

        def get_fd(self) -> int:
            return self.fd

        def get_events(self) -> int:
            return self.events

        def set_events(self, events: int):
            self.events = events

        def dispatch(self, events: int):
            self.cb(self.handle,
                    self.fd,
                    events,
                    self.opaque)

    # This class contains the data we need to track for a
    # single periodic timer
    class virEventLoopPollTimer:
        def __init__(self, timer: int, interval: int, cb: _TimerCallback, opaque: _T):
            self.timer = timer
            self.interval = interval
            self.cb = cb
            self.opaque = opaque
            self.lastfired = 0

        def get_id(self) -> int:
            return self.timer

        def get_interval(self) -> int:
            return self.interval

        def set_interval(self, interval: int):
            self.interval = interval

        def get_last_fired(self) -> int:
            return self.lastfired

        def set_last_fired(self, now: int):
            self.lastfired = now

        def dispatch(self) -> None:
            self.cb(self.timer,
                    self.opaque)

    def __init__(self):
        self.poll = select.poll()
        self.pipetrick = os.pipe()
        self.pendingWakeup = False
        self.runningPoll = False
        self.nextHandleID = 1
        self.nextTimerID = 1
        self.handles = []  # type: List[virEventLoopPollHandle]
        self.timers = []  # type: List[virEventLoopPollTimer]
        self.cleanup = []
        self.quit = False

        # The event loop can be used from multiple threads at once.
        # Specifically while the main thread is sleeping in poll()
        # waiting for events to occur, another thread may come along
        # and add/update/remove a file handle, or timer. When this
        # happens we need to interrupt the poll() sleep in the other
        # thread, so that it'll see the file handle / timer changes.
        #
        # Using OS level signals for this is very unreliable and
        # hard to implement correctly. Thus we use the real classic
        # "self pipe" trick. A anonymous pipe, with one end registered
        # with the event loop for input events. When we need to force
        # the main thread out of a poll() sleep, we simple write a
        # single byte of data to the other end of the pipe.
        debug("Self pipe watch %d write %d" % (self.pipetrick[0], self.pipetrick[1]))
        self.poll.register(self.pipetrick[0], select.POLLIN)

    # Calculate when the next timeout is due to occur, returning
    # the absolute timestamp for the next timeout, or 0 if there is
    # no timeout due
    def next_timeout(self) -> int:
        next = 0
        for t in self.timers:
            last = t.get_last_fired()
            interval = t.get_interval()
            if interval < 0:
                continue
            if next == 0 or (last + interval) < next:
                next = last + interval

        return next

    # Lookup a virEventLoopPollHandle object based on file descriptor
    def get_handle_by_fd(self, fd: int) -> Optional[virEventLoopPollHandle]:
        for h in self.handles:
            if h.get_fd() == fd:
                return h
        return None

    # Lookup a virEventLoopPollHandle object based on its event loop ID
    def get_handle_by_id(self, handleID: int) -> Optional[virEventLoopPollHandle]:
        for h in self.handles:
            if h.get_id() == handleID:
                return h
        return None

    # This is the heart of the event loop, performing one single
    # iteration. It asks when the next timeout is due, and then
    # calculates the maximum amount of time it is able to sleep
    # for in poll() pending file handle events.
    #
    # It then goes into the poll() sleep.
    #
    # When poll() returns, there will zero or more file handle
    # events which need to be dispatched to registered callbacks
    # It may also be time to fire some periodic timers.
    #
    # Due to the coarse granularity of scheduler timeslices, if
    # we ask for a sleep of 500ms in order to satisfy a timer, we
    # may return up to 1 scheduler timeslice early. So even though
    # our sleep timeout was reached, the registered timer may not
    # technically be at its expiry point. This leads to us going
    # back around the loop with a crazy 5ms sleep. So when checking
    # if timeouts are due, we allow a margin of 20ms, to avoid
    # these pointless repeated tiny sleeps.
    def run_once(self) -> None:
        sleep = -1  # type: float
        self.runningPoll = True

        for opaque in self.cleanup:
            libvirt.virEventInvokeFreeCallback(opaque)
        self.cleanup = []

        try:
            next = self.next_timeout()
            debug("Next timeout due at %d" % next)
            if next > 0:
                now = int(time.time() * 1000)
                if now >= next:
                    sleep = 0
                else:
                    sleep = (next - now) / 1000.0

            debug("Poll with a sleep of %d" % sleep)
            events = self.poll.poll(sleep)

            # Dispatch any file handle events that occurred
            for (fd, revents) in events:
                # See if the events was from the self-pipe
                # telling us to wakup. if so, then discard
                # the data just continue
                if fd == self.pipetrick[0]:
                    self.pendingWakeup = False
                    os.read(fd, 1)
                    continue

                h = self.get_handle_by_fd(fd)
                if h:
                    debug("Dispatch fd %d handle %d events %d" % (fd, h.get_id(), revents))
                    h.dispatch(self.events_from_poll(revents))

            now = int(time.time() * 1000)
            for t in self.timers:
                interval = t.get_interval()
                if interval < 0:
                    continue

                want = t.get_last_fired() + interval
                # Deduct 20ms, since scheduler timeslice
                # means we could be ever so slightly early
                if now >= want - 20:
                    debug("Dispatch timer %d now %s want %s" % (t.get_id(), str(now), str(want)))
                    t.set_last_fired(now)
                    t.dispatch()

        except (os.error, select.error) as e:
            if e.args[0] != errno.EINTR:
                raise
        finally:
            self.runningPoll = False

    # Actually run the event loop forever
    def run_loop(self) -> None:
        self.quit = False
        while not self.quit:
            self.run_once()

    def interrupt(self) -> None:
        if self.runningPoll and not self.pendingWakeup:
            self.pendingWakeup = True
            os.write(self.pipetrick[1], 'c'.encode("UTF-8"))

    # Registers a new file handle 'fd', monitoring  for 'events' (libvirt
    # event constants), firing the callback  cb() when an event occurs.
    # Returns a unique integer identier for this handle, that should be
    # used to later update/remove it
    def add_handle(self, fd: int, events: int, cb: _EventCallback, opaque: _T) -> int:
        handleID = self.nextHandleID + 1
        self.nextHandleID = self.nextHandleID + 1

        h = self.virEventLoopPollHandle(handleID, fd, events, cb, opaque)
        self.handles.append(h)

        self.poll.register(fd, self.events_to_poll(events))
        self.interrupt()

        debug("Add handle %d fd %d events %d" % (handleID, fd, events))

        return handleID

    # Registers a new timer with periodic expiry at 'interval' ms,
    # firing cb() each time the timer expires. If 'interval' is -1,
    # then the timer is registered, but not enabled
    # Returns a unique integer identier for this handle, that should be
    # used to later update/remove it
    def add_timer(self, interval: int, cb: _TimerCallback, opaque: _T) -> int:
        timerID = self.nextTimerID + 1
        self.nextTimerID = self.nextTimerID + 1

        h = self.virEventLoopPollTimer(timerID, interval, cb, opaque)
        self.timers.append(h)
        self.interrupt()

        debug("Add timer %d interval %d" % (timerID, interval))

        return timerID

    # Change the set of events to be monitored on the file handle
    def update_handle(self, handleID: int, events: int) -> None:
        h = self.get_handle_by_id(handleID)
        if h:
            h.set_events(events)
            self.poll.unregister(h.get_fd())
            self.poll.register(h.get_fd(), self.events_to_poll(events))
            self.interrupt()

            debug("Update handle %d fd %d events %d" % (handleID, h.get_fd(), events))

    # Change the periodic frequency of the timer
    def update_timer(self, timerID: int, interval: int) -> None:
        for h in self.timers:
            if h.get_id() == timerID:
                h.set_interval(interval)
                self.interrupt()

                debug("Update timer %d interval %d" % (timerID, interval))
                break

    # Stop monitoring for events on the file handle
    def remove_handle(self, handleID: int) -> int:
        handles = []
        for h in self.handles:
            if h.get_id() == handleID:
                debug("Remove handle %d fd %d" % (handleID, h.get_fd()))
                self.poll.unregister(h.get_fd())
                self.cleanup.append(h.opaque)
            else:
                handles.append(h)
        self.handles = handles
        self.interrupt()
        return 0

    # Stop firing the periodic timer
    def remove_timer(self, timerID: int) -> int:
        timers = []
        for h in self.timers:
            if h.get_id() != timerID:
                timers.append(h)
            else:
                debug("Remove timer %d" % timerID)
                self.cleanup.append(h.opaque)
        self.timers = timers
        self.interrupt()
        return 0

    # Convert from libvirt event constants, to poll() events constants
    def events_to_poll(self, events: int) -> int:
        ret = 0
        if events & libvirt.VIR_EVENT_HANDLE_READABLE:
            ret |= select.POLLIN
        if events & libvirt.VIR_EVENT_HANDLE_WRITABLE:
            ret |= select.POLLOUT
        if events & libvirt.VIR_EVENT_HANDLE_ERROR:
            ret |= select.POLLERR
        if events & libvirt.VIR_EVENT_HANDLE_HANGUP:
            ret |= select.POLLHUP
        return ret

    # Convert from poll() event constants, to libvirt events constants
    def events_from_poll(self, events: int) -> int:
        ret = 0
        if events & select.POLLIN:
            ret |= libvirt.VIR_EVENT_HANDLE_READABLE
        if events & select.POLLOUT:
            ret |= libvirt.VIR_EVENT_HANDLE_WRITABLE
        if events & select.POLLNVAL:
            ret |= libvirt.VIR_EVENT_HANDLE_ERROR
        if events & select.POLLERR:
            ret |= libvirt.VIR_EVENT_HANDLE_ERROR
        if events & select.POLLHUP:
            ret |= libvirt.VIR_EVENT_HANDLE_HANGUP
        return ret


###########################################################################
# Now glue an instance of the general event loop into libvirt's event loop
###########################################################################

# This single global instance of the event loop wil be used for
# monitoring libvirt events
eventLoop = virEventLoopPoll()

# This keeps track of what thread is running the event loop,
# (if it is run in a background thread)
eventLoopThread = None


# These next set of 6 methods are the glue between the official
# libvirt events API, and our particular impl of the event loop
#
# There is no reason why the 'virEventLoopPoll' has to be used.
# An application could easily may these 6 glue methods hook into
# another event loop such as GLib's, or something like the python
# Twisted event framework.

def virEventAddHandleImpl(fd: int, events: int, cb: _EventCallback, opaque: _T) -> int:
    return eventLoop.add_handle(fd, events, cb, opaque)


def virEventUpdateHandleImpl(handleID: int, events: int) -> None:
    return eventLoop.update_handle(handleID, events)


def virEventRemoveHandleImpl(handleID: int) -> int:
    return eventLoop.remove_handle(handleID)


def virEventAddTimerImpl(interval: int, cb: _TimerCallback, opaque: _T) -> int:
    return eventLoop.add_timer(interval, cb, opaque)


def virEventUpdateTimerImpl(timerID: int, interval: int) -> None:
    return eventLoop.update_timer(timerID, interval)


def virEventRemoveTimerImpl(timerID: int) -> int:
    return eventLoop.remove_timer(timerID)


# This tells libvirt what event loop implementation it
# should use
def virEventLoopPollRegister() -> None:
    libvirt.virEventRegisterImpl(virEventAddHandleImpl,
                                 virEventUpdateHandleImpl,
                                 virEventRemoveHandleImpl,
                                 virEventAddTimerImpl,
                                 virEventUpdateTimerImpl,
                                 virEventRemoveTimerImpl)


# Directly run the event loop in the current thread
def virEventLoopPollRun() -> None:
    eventLoop.run_loop()


def virEventLoopAIORun(loop) -> None:
    import asyncio
    asyncio.set_event_loop(loop)
    loop.run_forever()


def virEventLoopNativeRun() -> None:
    while True:
        libvirt.virEventRunDefaultImpl()


# Spawn a background thread to run the event loop
def virEventLoopPollStart() -> None:
    global eventLoopThread
    virEventLoopPollRegister()
    eventLoopThread = threading.Thread(target=virEventLoopPollRun, name="libvirtEventLoop")
    eventLoopThread.setDaemon(True)
    eventLoopThread.start()


def virEventLoopAIOStart() -> None:
    global eventLoopThread
    import libvirtaio
    import asyncio
    loop = asyncio.new_event_loop()
    libvirtaio.virEventRegisterAsyncIOImpl(loop=loop)
    eventLoopThread = threading.Thread(target=virEventLoopAIORun, args=(loop,), name="libvirtEventLoop")
    eventLoopThread.setDaemon(True)
    eventLoopThread.start()


def virEventLoopNativeStart() -> None:
    global eventLoopThread
    libvirt.virEventRegisterDefaultImpl()
    eventLoopThread = threading.Thread(target=virEventLoopNativeRun, name="libvirtEventLoop")
    eventLoopThread.setDaemon(True)
    eventLoopThread.start()


##########################################################################
# Everything that now follows is a simple demo of domain lifecycle events
##########################################################################
class Description(object):
    __slots__ = ('desc', 'args')

    def __init__(self, *args, **kwargs) -> None:
        self.desc = kwargs.get('desc')
        self.args = args

    def __str__(self) -> str:
        return self.desc or ''

    def __getitem__(self, item: int) -> 'Description':
        try:
            data = self.args[item]
        except IndexError:
            return self.__class__(desc=str(item))

        if isinstance(data, str):
            return self.__class__(desc=data)
        elif isinstance(data, (list, tuple)):
            desc, args = data
            return self.__class__(*args, desc=desc)

        raise TypeError(args)


DOM_EVENTS = Description(
    ("Defined", ("Added", "Updated", "Renamed", "Snapshot")),
    ("Undefined", ("Removed", "Renamed")),
    ("Started", ("Booted", "Migrated", "Restored", "Snapshot", "Wakeup")),
    ("Suspended", ("Paused", "Migrated", "IOError", "Watchdog", "Restored", "Snapshot", "API error", "Postcopy", "Postcopy failed")),
    ("Resumed", ("Unpaused", "Migrated", "Snapshot", "Postcopy")),
    ("Stopped", ("Shutdown", "Destroyed", "Crashed", "Migrated", "Saved", "Failed", "Snapshot", "Daemon")),
    ("Shutdown", ("Finished", "On guest request", "On host request")),
    ("PMSuspended", ("Memory", "Disk")),
    ("Crashed", ("Panicked",)),
)
BLOCK_JOB_TYPES = Description("unknown", "Pull", "Copy", "Commit", "ActiveCommit")
BLOCK_JOB_STATUS = Description("Completed", "Failed", "Canceled", "Ready")
WATCHDOG_ACTIONS = Description("none", "Pause", "Reset", "Poweroff", "Shutdown", "Debug", "Inject NMI")
ERROR_EVENTS = Description("None", "Pause", "Report")
AGENT_STATES = Description("unknown", "connected", "disconnected")
AGENT_REASONS = Description("unknown", "domain started", "channel event")
GRAPHICS_PHASES = Description("Connect", "Initialize", "Disconnect")
DISK_EVENTS = Description("Change missing on start", "Drop missing on start")
TRAY_EVENTS = Description("Opened", "Closed")


def myDomainEventCallback(conn: libvirt.virConnect, dom: libvirt.virDomain, event: int, detail: int, opaque: _T) -> None:
    print("myDomainEventCallback%s EVENT: Domain %s(%s) %s %s" % (
        opaque, dom.name(), dom.ID(), DOM_EVENTS[event], DOM_EVENTS[event][detail]))


def myDomainEventRebootCallback(conn: libvirt.virConnect, dom: libvirt.virDomain, opaque: _T) -> None:
    print("myDomainEventRebootCallback: Domain %s(%s)" % (
        dom.name(), dom.ID()))


def myDomainEventRTCChangeCallback(conn: libvirt.virConnect, dom: libvirt.virDomain, utcoffset: int, opaque: _T) -> None:
    print("myDomainEventRTCChangeCallback: Domain %s(%s) %d" % (
        dom.name(), dom.ID(), utcoffset))


def myDomainEventWatchdogCallback(conn: libvirt.virConnect, dom: libvirt.virDomain, action: int, opaque: _T) -> None:
    print("myDomainEventWatchdogCallback: Domain %s(%s) %s" % (
        dom.name(), dom.ID(), WATCHDOG_ACTIONS[action]))


def myDomainEventIOErrorCallback(conn: libvirt.virConnect, dom: libvirt.virDomain, srcpath: str, devalias: str, action: int, opaque: _T) -> None:
    print("myDomainEventIOErrorCallback: Domain %s(%s) %s %s %s" % (
        dom.name(), dom.ID(), srcpath, devalias, ERROR_EVENTS[action]))


def myDomainEventIOErrorReasonCallback(conn: libvirt.virConnect, dom: libvirt.virDomain, srcpath: str, devalias: str, action: int, reason: int, opaque: _T) -> None:
    print("myDomainEventIOErrorReasonCallback: Domain %s(%s) %s %s %s %s" % (
        dom.name(), dom.ID(), srcpath, devalias, ERROR_EVENTS[action], reason))


def myDomainEventGraphicsCallback(conn: libvirt.virConnect, dom: libvirt.virDomain, phase: int, localAddr: str, remoteAddr: str, authScheme: str, subject: str, opaque: _T) -> None:
    print("myDomainEventGraphicsCallback: Domain %s(%s) %s %s" % (
        dom.name(), dom.ID(), GRAPHICS_PHASES[phase], authScheme))


def myDomainEventControlErrorCallback(conn: libvirt.virConnect, dom: libvirt.virDomain, opaque: _T) -> None:
    print("myDomainEventControlErrorCallback: Domain %s(%s)" % (
        dom.name(), dom.ID()))


def myDomainEventBlockJobCallback(conn: libvirt.virConnect, dom: libvirt.virDomain, disk, type: int, status: int, opaque: _T) -> None:
    print("myDomainEventBlockJobCallback: Domain %s(%s) %s on disk %s %s" % (
        dom.name(), dom.ID(), BLOCK_JOB_TYPES[type], disk, BLOCK_JOB_STATUS[status]))


def myDomainEventDiskChangeCallback(conn: libvirt.virConnect, dom: libvirt.virDomain, oldSrcPath: str, newSrcPath: str, devAlias: str, reason: int, opaque: _T) -> None:
    print("myDomainEventDiskChangeCallback: Domain %s(%s) disk change oldSrcPath: %s newSrcPath: %s devAlias: %s reason: %s" % (
        dom.name(), dom.ID(), oldSrcPath, newSrcPath, devAlias, DISK_EVENTS[reason]))


def myDomainEventTrayChangeCallback(conn: libvirt.virConnect, dom: libvirt.virDomain, devAlias: str, reason: int, opaque: _T) -> None:
    print("myDomainEventTrayChangeCallback: Domain %s(%s) tray change devAlias: %s reason: %s" % (
        dom.name(), dom.ID(), devAlias, TRAY_EVENTS[reason]))


def myDomainEventPMWakeupCallback(conn: libvirt.virConnect, dom: libvirt.virDomain, reason: int, opaque: _T) -> None:
    print("myDomainEventPMWakeupCallback: Domain %s(%s) system pmwakeup" % (
        dom.name(), dom.ID()))


def myDomainEventPMSuspendCallback(conn: libvirt.virConnect, dom: libvirt.virDomain, reason: int, opaque: _T) -> None:
    print("myDomainEventPMSuspendCallback: Domain %s(%s) system pmsuspend" % (
        dom.name(), dom.ID()))


def myDomainEventBalloonChangeCallback(conn: libvirt.virConnect, dom: libvirt.virDomain, actual: int, opaque: _T) -> None:
    print("myDomainEventBalloonChangeCallback: Domain %s(%s) %d" % (
        dom.name(), dom.ID(), actual))


def myDomainEventPMSuspendDiskCallback(conn: libvirt.virConnect, dom: libvirt.virDomain, reason: int, opaque: _T) -> None:
    print("myDomainEventPMSuspendDiskCallback: Domain %s(%s) system pmsuspend_disk" % (
        dom.name(), dom.ID()))


def myDomainEventDeviceRemovedCallback(conn: libvirt.virConnect, dom: libvirt.virDomain, dev: str, opaque: _T) -> None:
    print("myDomainEventDeviceRemovedCallback: Domain %s(%s) device removed: %s" % (
        dom.name(), dom.ID(), dev))


def myDomainEventBlockJob2Callback(conn: libvirt.virConnect, dom: libvirt.virDomain, disk: str, type: int, status: int, opaque: _T) -> None:
    print("myDomainEventBlockJob2Callback: Domain %s(%s) %s on disk %s %s" % (
        dom.name(), dom.ID(), BLOCK_JOB_TYPES[type], disk, BLOCK_JOB_STATUS[status]))


def myDomainEventTunableCallback(conn: libvirt.virConnect, dom: libvirt.virDomain, params: Dict[str, Any], opaque: _T) -> None:
    print("myDomainEventTunableCallback: Domain %s(%s) %s" % (
        dom.name(), dom.ID(), params))


def myDomainEventAgentLifecycleCallback(conn: libvirt.virConnect, dom: libvirt.virDomain, state: int, reason: int, opaque: _T) -> None:
    print("myDomainEventAgentLifecycleCallback: Domain %s(%s) %s %s" % (
        dom.name(), dom.ID(), AGENT_STATES[state], AGENT_REASONS[reason]))


def myDomainEventDeviceAddedCallback(conn: libvirt.virConnect, dom: libvirt.virDomain, dev: str, opaque: _T) -> None:
    print("myDomainEventDeviceAddedCallback: Domain %s(%s) device added: %s" % (
        dom.name(), dom.ID(), dev))


def myDomainEventMigrationIteration(conn: libvirt.virConnect, dom: libvirt.virDomain, iteration: int, opaque: _T) -> None:
    print("myDomainEventMigrationIteration: Domain %s(%s) started migration iteration %d" % (
        dom.name(), dom.ID(), iteration))


def myDomainEventJobCompletedCallback(conn: libvirt.virConnect, dom: libvirt.virDomain, params: Dict[str, Any], opaque: _T) -> None:
    print("myDomainEventJobCompletedCallback: Domain %s(%s) %s" % (
        dom.name(), dom.ID(), params))


def myDomainEventDeviceRemovalFailedCallback(conn: libvirt.virConnect, dom: libvirt.virDomain, dev: str, opaque: _T) -> None:
    print("myDomainEventDeviceRemovalFailedCallback: Domain %s(%s) failed to remove device: %s" % (
        dom.name(), dom.ID(), dev))


def myDomainEventMetadataChangeCallback(conn: libvirt.virConnect, dom: libvirt.virDomain, mtype: int, nsuri: str, opaque: _T) -> None:
    print("myDomainEventMetadataChangeCallback: Domain %s(%s) changed metadata mtype=%d nsuri=%s" % (
        dom.name(), dom.ID(), mtype, nsuri))


def myDomainEventBlockThresholdCallback(conn: libvirt.virConnect, dom: libvirt.virDomain, dev: str, path: str, threshold: int, excess: int, opaque: _T) -> None:
    print("myDomainEventBlockThresholdCallback: Domain %s(%s) block device %s(%s) threshold %d exceeded by %d" % (
        dom.name(), dom.ID(), dev, path, threshold, excess))

def myDomainEventMemoryFailureCallback(conn: libvirt.virConnect, dom: libvirt.virDomain, recipient: int, action: int, flags: int, opaque: _T) -> None:
    print("myDomainEventMemoryFailureCallback: Domain %s(%s) memory failure recipient %d action %d flags %d" % (
        dom.name(), dom.ID(), recipient, action, flags))


##########################################################################
# Network events
##########################################################################
NET_EVENTS = Description(
    ("Defined", ("Added",)),
    ("Undefined", ("Removed",)),
    ("Started", ("Started",)),
    ("Stopped", ("Stopped",)),
)


def myNetworkEventLifecycleCallback(conn: libvirt.virConnect, net: libvirt.virNetwork, event: int, detail: int, opaque: _T) -> None:
    print("myNetworkEventLifecycleCallback: Network %s %s %s" % (
        net.name(), NET_EVENTS[event], NET_EVENTS[event][detail]))


##########################################################################
# Storage pool events
##########################################################################
STORAGE_EVENTS = Description(
    ("Defined", ()),
    ("Undefined", ()),
    ("Started", ()),
    ("Stopped", ()),
    ("Created", ()),
    ("Deleted", ()),
)


def myStoragePoolEventLifecycleCallback(conn: libvirt.virConnect, pool: libvirt.virStoragePool, event: int, detail: int, opaque: _T) -> None:
    print("myStoragePoolEventLifecycleCallback: Storage pool %s %s %s" % (
        pool.name(), STORAGE_EVENTS[event], STORAGE_EVENTS[event][detail]))


def myStoragePoolEventRefreshCallback(conn: libvirt.virConnect, pool: libvirt.virStoragePool, opaque: _T) -> None:
    print("myStoragePoolEventRefreshCallback: Storage pool %s" % pool.name())


##########################################################################
# Node device events
##########################################################################
DEVICE_EVENTS = Description(
    ("Created", ()),
    ("Deleted", ()),
)


def myNodeDeviceEventLifecycleCallback(conn: libvirt.virConnect, dev: libvirt.virNodeDevice, event: int, detail: int, opaque: _T) -> None:
    print("myNodeDeviceEventLifecycleCallback: Node device  %s %s %s" % (
        dev.name(), DEVICE_EVENTS[event], DEVICE_EVENTS[event][detail]))


def myNodeDeviceEventUpdateCallback(conn: libvirt.virConnect, dev: libvirt.virNodeDevice, opaque: _T) -> None:
    print("myNodeDeviceEventUpdateCallback: Node device %s" % dev.name())


##########################################################################
# Secret events
##########################################################################
SECRET_EVENTS = Description(
    ("Defined", ()),
    ("Undefined", ()),
)


def mySecretEventLifecycleCallback(conn: libvirt.virConnect, secret: libvirt.virSecret, event: int, detail: int, opaque: _T) -> None:
    print("mySecretEventLifecycleCallback: Secret %s %s %s" % (
        secret.UUIDString(), SECRET_EVENTS[event], SECRET_EVENTS[event][detail]))


def mySecretEventValueChanged(conn: libvirt.virConnect, secret: libvirt.virSecret, opaque: _T) -> None:
    print("mySecretEventValueChanged: Secret %s" % secret.UUIDString())


##########################################################################
# Set up and run the program
##########################################################################

run = True
CONNECTION_EVENTS = Description("Error", "End-of-file", "Keepalive", "Client")


def myConnectionCloseCallback(conn: libvirt.virConnect, reason: int, opaque: _T) -> None:
    print("myConnectionCloseCallback: %s: %s" % (
        conn.getURI(), CONNECTION_EVENTS[reason]))
    global run
    run = False


def main() -> None:
    parser = ArgumentParser()
    parser.add_argument("--debug", "-d", action="store_true", help="Print debug output")
    parser.add_argument("--loop", "-l", choices=("native", "poll", "asyncio"), default=event_impl, help="Choose event-loop-implementation")
    parser.add_argument("--timeout", type=int, default=None, help="Quit after SECS seconds running")
    parser.add_argument("uri", nargs="?", default="qemu:///system")
    args = parser.parse_args()

    if args.debug:
            global do_debug
            do_debug = True

    print("Using uri '%s' and event loop '%s'" % (args.uri, args.loop))

    # Run a background thread with the event loop
    if args.loop == "poll":
        virEventLoopPollStart()
    elif args.loop == "asyncio":
        virEventLoopAIOStart()
    else:
        virEventLoopNativeStart()

    vc = libvirt.openReadOnly(args.uri)

    # Close connection on exit (to test cleanup paths)
    def exit() -> None:
        print("Closing " + vc.getURI())
        if run:
            vc.close()

    atexit.register(exit)

    vc.registerCloseCallback(myConnectionCloseCallback, None)

    # Add 2 lifecycle callbacks to prove this works with more than just one
    vc.domainEventRegister(myDomainEventCallback, 1)
    domcallbacks = [
        vc.domainEventRegisterAny(None, libvirt.VIR_DOMAIN_EVENT_ID_LIFECYCLE, myDomainEventCallback, 2),
        vc.domainEventRegisterAny(None, libvirt.VIR_DOMAIN_EVENT_ID_REBOOT, myDomainEventRebootCallback, None),
        vc.domainEventRegisterAny(None, libvirt.VIR_DOMAIN_EVENT_ID_RTC_CHANGE, myDomainEventRTCChangeCallback, None),
        vc.domainEventRegisterAny(None, libvirt.VIR_DOMAIN_EVENT_ID_WATCHDOG, myDomainEventWatchdogCallback, None),
        vc.domainEventRegisterAny(None, libvirt.VIR_DOMAIN_EVENT_ID_IO_ERROR, myDomainEventIOErrorCallback, None),
        vc.domainEventRegisterAny(None, libvirt.VIR_DOMAIN_EVENT_ID_GRAPHICS, myDomainEventGraphicsCallback, None),
        vc.domainEventRegisterAny(None, libvirt.VIR_DOMAIN_EVENT_ID_IO_ERROR_REASON, myDomainEventIOErrorReasonCallback, None),
        vc.domainEventRegisterAny(None, libvirt.VIR_DOMAIN_EVENT_ID_CONTROL_ERROR, myDomainEventControlErrorCallback, None),
        vc.domainEventRegisterAny(None, libvirt.VIR_DOMAIN_EVENT_ID_BLOCK_JOB, myDomainEventBlockJobCallback, None),
        vc.domainEventRegisterAny(None, libvirt.VIR_DOMAIN_EVENT_ID_DISK_CHANGE, myDomainEventDiskChangeCallback, None),
        vc.domainEventRegisterAny(None, libvirt.VIR_DOMAIN_EVENT_ID_TRAY_CHANGE, myDomainEventTrayChangeCallback, None),
        vc.domainEventRegisterAny(None, libvirt.VIR_DOMAIN_EVENT_ID_PMWAKEUP, myDomainEventPMWakeupCallback, None),
        vc.domainEventRegisterAny(None, libvirt.VIR_DOMAIN_EVENT_ID_PMSUSPEND, myDomainEventPMSuspendCallback, None),
        vc.domainEventRegisterAny(None, libvirt.VIR_DOMAIN_EVENT_ID_BALLOON_CHANGE, myDomainEventBalloonChangeCallback, None),
        vc.domainEventRegisterAny(None, libvirt.VIR_DOMAIN_EVENT_ID_PMSUSPEND_DISK, myDomainEventPMSuspendDiskCallback, None),
        vc.domainEventRegisterAny(None, libvirt.VIR_DOMAIN_EVENT_ID_DEVICE_REMOVED, myDomainEventDeviceRemovedCallback, None),
        vc.domainEventRegisterAny(None, libvirt.VIR_DOMAIN_EVENT_ID_BLOCK_JOB_2, myDomainEventBlockJob2Callback, None),
        vc.domainEventRegisterAny(None, libvirt.VIR_DOMAIN_EVENT_ID_TUNABLE, myDomainEventTunableCallback, None),
        vc.domainEventRegisterAny(None, libvirt.VIR_DOMAIN_EVENT_ID_AGENT_LIFECYCLE, myDomainEventAgentLifecycleCallback, None),
        vc.domainEventRegisterAny(None, libvirt.VIR_DOMAIN_EVENT_ID_DEVICE_ADDED, myDomainEventDeviceAddedCallback, None),
        vc.domainEventRegisterAny(None, libvirt.VIR_DOMAIN_EVENT_ID_MIGRATION_ITERATION, myDomainEventMigrationIteration, None),
        vc.domainEventRegisterAny(None, libvirt.VIR_DOMAIN_EVENT_ID_JOB_COMPLETED, myDomainEventJobCompletedCallback, None),
        vc.domainEventRegisterAny(None, libvirt.VIR_DOMAIN_EVENT_ID_DEVICE_REMOVAL_FAILED, myDomainEventDeviceRemovalFailedCallback, None),
        vc.domainEventRegisterAny(None, libvirt.VIR_DOMAIN_EVENT_ID_METADATA_CHANGE, myDomainEventMetadataChangeCallback, None),
        vc.domainEventRegisterAny(None, libvirt.VIR_DOMAIN_EVENT_ID_BLOCK_THRESHOLD, myDomainEventBlockThresholdCallback, None),
        vc.domainEventRegisterAny(None, libvirt.VIR_DOMAIN_EVENT_ID_MEMORY_FAILURE, myDomainEventMemoryFailureCallback, None),
    ]

    netcallbacks = [
        vc.networkEventRegisterAny(None, libvirt.VIR_NETWORK_EVENT_ID_LIFECYCLE, myNetworkEventLifecycleCallback, None),
    ]

    poolcallbacks = [
        vc.storagePoolEventRegisterAny(None, libvirt.VIR_STORAGE_POOL_EVENT_ID_LIFECYCLE, myStoragePoolEventLifecycleCallback, None),
        vc.storagePoolEventRegisterAny(None, libvirt.VIR_STORAGE_POOL_EVENT_ID_REFRESH, myStoragePoolEventRefreshCallback, None),
    ]

    devcallbacks = [
        vc.nodeDeviceEventRegisterAny(None, libvirt.VIR_NODE_DEVICE_EVENT_ID_LIFECYCLE, myNodeDeviceEventLifecycleCallback, None),
        vc.nodeDeviceEventRegisterAny(None, libvirt.VIR_NODE_DEVICE_EVENT_ID_UPDATE, myNodeDeviceEventUpdateCallback, None),
    ]

    seccallbacks = [
        vc.secretEventRegisterAny(None, libvirt.VIR_SECRET_EVENT_ID_LIFECYCLE, mySecretEventLifecycleCallback, None),
        vc.secretEventRegisterAny(None, libvirt.VIR_SECRET_EVENT_ID_VALUE_CHANGED, mySecretEventValueChanged, None),
    ]

    vc.setKeepAlive(5, 3)

    # The rest of your app would go here normally, but for sake
    # of demo we'll just go to sleep. The other option is to
    # run the event loop in your main thread if your app is
    # totally event based.
    count = 0
    while run and (args.timeout is None or count < args.timeout):
        count = count + 1
        time.sleep(1)

    # If the connection was closed, we cannot unregister anything.
    # Just abort now.
    if not run:
        return

    vc.domainEventDeregister(myDomainEventCallback)

    for id in seccallbacks:
        vc.secretEventDeregisterAny(id)
    for id in devcallbacks:
        vc.nodeDeviceEventDeregisterAny(id)
    for id in poolcallbacks:
        vc.storagePoolEventDeregisterAny(id)
    for id in netcallbacks:
        vc.networkEventDeregisterAny(id)
    for id in domcallbacks:
        vc.domainEventDeregisterAny(id)

    vc.unregisterCloseCallback()
    vc.close()

    # Allow delayed event loop cleanup to run, just for sake of testing
    time.sleep(2)


if __name__ == "__main__":
    main()
