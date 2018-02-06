#!/usr/bin/env python
#
#
#
##############################################################################
# Start off by implementing a general purpose event loop for anyone's use
##############################################################################

import sys
import getopt
import os
import libvirt
import select
import errno
import time
import threading

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
def debug(msg):
    global do_debug
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
        def __init__(self, handle, fd, events, cb, opaque):
            self.handle = handle
            self.fd = fd
            self.events = events
            self.cb = cb
            self.opaque = opaque

        def get_id(self):
            return self.handle

        def get_fd(self):
            return self.fd

        def get_events(self):
            return self.events

        def set_events(self, events):
            self.events = events

        def dispatch(self, events):
            self.cb(self.handle,
                    self.fd,
                    events,
                    self.opaque)

    # This class contains the data we need to track for a
    # single periodic timer
    class virEventLoopPollTimer:
        def __init__(self, timer, interval, cb, opaque):
            self.timer = timer
            self.interval = interval
            self.cb = cb
            self.opaque = opaque
            self.lastfired = 0

        def get_id(self):
            return self.timer

        def get_interval(self):
            return self.interval

        def set_interval(self, interval):
            self.interval = interval

        def get_last_fired(self):
            return self.lastfired

        def set_last_fired(self, now):
            self.lastfired = now

        def dispatch(self):
            self.cb(self.timer,
                    self.opaque)


    def __init__(self):
        self.poll = select.poll()
        self.pipetrick = os.pipe()
        self.pendingWakeup = False
        self.runningPoll = False
        self.nextHandleID = 1
        self.nextTimerID = 1
        self.handles = []
        self.timers = []
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
        debug("Self pipe watch %d write %d" %(self.pipetrick[0], self.pipetrick[1]))
        self.poll.register(self.pipetrick[0], select.POLLIN)


    # Calculate when the next timeout is due to occur, returning
    # the absolute timestamp for the next timeout, or 0 if there is
    # no timeout due
    def next_timeout(self):
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
    def get_handle_by_fd(self, fd):
        for h in self.handles:
            if h.get_fd() == fd:
                return h
        return None

    # Lookup a virEventLoopPollHandle object based on its event loop ID
    def get_handle_by_id(self, handleID):
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
    def run_once(self):
        sleep = -1
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
                    data = os.read(fd, 1)
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
                if now >= (want-20):
                    debug("Dispatch timer %d now %s want %s" % (t.get_id(), str(now), str(want)))
                    t.set_last_fired(now)
                    t.dispatch()

        except (os.error, select.error) as e:
            if e.args[0] != errno.EINTR:
                raise
        finally:
            self.runningPoll = False


    # Actually run the event loop forever
    def run_loop(self):
        self.quit = False
        while not self.quit:
            self.run_once()

    def interrupt(self):
        if self.runningPoll and not self.pendingWakeup:
            self.pendingWakeup = True
            os.write(self.pipetrick[1], 'c'.encode("UTF-8"))


    # Registers a new file handle 'fd', monitoring  for 'events' (libvirt
    # event constants), firing the callback  cb() when an event occurs.
    # Returns a unique integer identier for this handle, that should be
    # used to later update/remove it
    def add_handle(self, fd, events, cb, opaque):
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
    def add_timer(self, interval, cb, opaque):
        timerID = self.nextTimerID + 1
        self.nextTimerID = self.nextTimerID + 1

        h = self.virEventLoopPollTimer(timerID, interval, cb, opaque)
        self.timers.append(h)
        self.interrupt()

        debug("Add timer %d interval %d" % (timerID, interval))

        return timerID

    # Change the set of events to be monitored on the file handle
    def update_handle(self, handleID, events):
        h = self.get_handle_by_id(handleID)
        if h:
            h.set_events(events)
            self.poll.unregister(h.get_fd())
            self.poll.register(h.get_fd(), self.events_to_poll(events))
            self.interrupt()

            debug("Update handle %d fd %d events %d" % (handleID, h.get_fd(), events))

    # Change the periodic frequency of the timer
    def update_timer(self, timerID, interval):
        for h in self.timers:
            if h.get_id() == timerID:
                h.set_interval(interval)
                self.interrupt()

                debug("Update timer %d interval %d"  % (timerID, interval))
                break

    # Stop monitoring for events on the file handle
    def remove_handle(self, handleID):
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

    # Stop firing the periodic timer
    def remove_timer(self, timerID):
        timers = []
        for h in self.timers:
            if h.get_id() != timerID:
                timers.append(h)
            else:
                debug("Remove timer %d" % timerID)
                self.cleanup.append(h.opaque)
        self.timers = timers
        self.interrupt()

    # Convert from libvirt event constants, to poll() events constants
    def events_to_poll(self, events):
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
    def events_from_poll(self, events):
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

def virEventAddHandleImpl(fd, events, cb, opaque):
    global eventLoop
    return eventLoop.add_handle(fd, events, cb, opaque)

def virEventUpdateHandleImpl(handleID, events):
    global eventLoop
    return eventLoop.update_handle(handleID, events)

def virEventRemoveHandleImpl(handleID):
    global eventLoop
    return eventLoop.remove_handle(handleID)

def virEventAddTimerImpl(interval, cb, opaque):
    global eventLoop
    return eventLoop.add_timer(interval, cb, opaque)

def virEventUpdateTimerImpl(timerID, interval):
    global eventLoop
    return eventLoop.update_timer(timerID, interval)

def virEventRemoveTimerImpl(timerID):
    global eventLoop
    return eventLoop.remove_timer(timerID)

# This tells libvirt what event loop implementation it
# should use
def virEventLoopPollRegister():
    libvirt.virEventRegisterImpl(virEventAddHandleImpl,
                                 virEventUpdateHandleImpl,
                                 virEventRemoveHandleImpl,
                                 virEventAddTimerImpl,
                                 virEventUpdateTimerImpl,
                                 virEventRemoveTimerImpl)

# Directly run the event loop in the current thread
def virEventLoopPollRun():
    global eventLoop
    eventLoop.run_loop()

def virEventLoopAIORun(loop):
    import asyncio
    asyncio.set_event_loop(loop)
    loop.run_forever()

def virEventLoopNativeRun():
    while True:
        libvirt.virEventRunDefaultImpl()

# Spawn a background thread to run the event loop
def virEventLoopPollStart():
    global eventLoopThread
    virEventLoopPollRegister()
    eventLoopThread = threading.Thread(target=virEventLoopPollRun, name="libvirtEventLoop")
    eventLoopThread.setDaemon(True)
    eventLoopThread.start()

def virEventLoopAIOStart():
    global eventLoopThread
    import libvirtaio
    import asyncio
    loop = asyncio.new_event_loop()
    libvirtaio.virEventRegisterAsyncIOImpl(loop=loop)
    eventLoopThread = threading.Thread(target=virEventLoopAIORun, args=(loop,), name="libvirtEventLoop")
    eventLoopThread.setDaemon(True)
    eventLoopThread.start()

def virEventLoopNativeStart():
    global eventLoopThread
    libvirt.virEventRegisterDefaultImpl()
    eventLoopThread = threading.Thread(target=virEventLoopNativeRun, name="libvirtEventLoop")
    eventLoopThread.setDaemon(True)
    eventLoopThread.start()


##########################################################################
# Everything that now follows is a simple demo of domain lifecycle events
##########################################################################
def domEventToString(event):
    domEventStrings = ( "Defined",
                     "Undefined",
                     "Started",
                     "Suspended",
                     "Resumed",
                     "Stopped",
                     "Shutdown",
                     "PMSuspended",
                     "Crashed",
    )
    return domEventStrings[event]

def domDetailToString(event, detail):
    domEventStrings = (
        ( "Added", "Updated" ),
        ( "Removed", ),
        ( "Booted", "Migrated", "Restored", "Snapshot", "Wakeup" ),
        ( "Paused", "Migrated", "IOError", "Watchdog", "Restored", "Snapshot", "API error" ),
        ( "Unpaused", "Migrated", "Snapshot" ),
        ( "Shutdown", "Destroyed", "Crashed", "Migrated", "Saved", "Failed", "Snapshot"),
        ( "Finished", "On guest request", "On host request"),
        ( "Memory", "Disk" ),
        ( "Panicked", ),
        )
    return domEventStrings[event][detail]

def blockJobTypeToString(type):
    blockJobTypes = ( "unknown", "Pull", "Copy", "Commit", "ActiveCommit", )
    return blockJobTypes[type]

def blockJobStatusToString(status):
    blockJobStatus = ( "Completed", "Failed", "Canceled", "Ready", )
    return blockJobStatus[status]

def agentLifecycleStateToString(state):
    agentStates = ( "unknown", "connected", "disconnected", )
    return agentStates[state]

def agentLifecycleReasonToString(reason):
    agentReasons = ( "unknown", "domain started", "channel event", )
    return agentReasons[reason]

def myDomainEventCallback1 (conn, dom, event, detail, opaque):
    print("myDomainEventCallback1 EVENT: Domain %s(%s) %s %s" % (dom.name(), dom.ID(),
                                                                 domEventToString(event),
                                                                 domDetailToString(event, detail)))

def myDomainEventCallback2 (conn, dom, event, detail, opaque):
    print("myDomainEventCallback2 EVENT: Domain %s(%s) %s %s" % (dom.name(), dom.ID(),
                                                                 domEventToString(event),
                                                                 domDetailToString(event, detail)))

def myDomainEventRebootCallback(conn, dom, opaque):
    print("myDomainEventRebootCallback: Domain %s(%s)" % (dom.name(), dom.ID()))

def myDomainEventRTCChangeCallback(conn, dom, utcoffset, opaque):
    print("myDomainEventRTCChangeCallback: Domain %s(%s) %d" % (dom.name(), dom.ID(), utcoffset))

def myDomainEventWatchdogCallback(conn, dom, action, opaque):
    print("myDomainEventWatchdogCallback: Domain %s(%s) %d" % (dom.name(), dom.ID(), action))

def myDomainEventIOErrorCallback(conn, dom, srcpath, devalias, action, opaque):
    print("myDomainEventIOErrorCallback: Domain %s(%s) %s %s %d" % (dom.name(), dom.ID(), srcpath, devalias, action))
def myDomainEventIOErrorReasonCallback(conn, dom, srcpath, devalias, action, reason, opaque):
    print("myDomainEventIOErrorReasonCallback: Domain %s(%s) %s %s %d %s" % (dom.name(), dom.ID(), srcpath, devalias, action, reason))
def myDomainEventGraphicsCallback(conn, dom, phase, localAddr, remoteAddr, authScheme, subject, opaque):
    print("myDomainEventGraphicsCallback: Domain %s(%s) %d %s" % (dom.name(), dom.ID(), phase, authScheme))
def myDomainEventControlErrorCallback(conn, dom, opaque):
    print("myDomainEventControlErrorCallback: Domain %s(%s)" % (dom.name(), dom.ID()))
def myDomainEventBlockJobCallback(conn, dom, disk, type, status, opaque):
    print("myDomainEventBlockJobCallback: Domain %s(%s) %s on disk %s %s" % (dom.name(), dom.ID(), blockJobTypeToString(type), disk, blockJobStatusToString(status)))
def myDomainEventDiskChangeCallback(conn, dom, oldSrcPath, newSrcPath, devAlias, reason, opaque):
    print("myDomainEventDiskChangeCallback: Domain %s(%s) disk change oldSrcPath: %s newSrcPath: %s devAlias: %s reason: %s" % (
            dom.name(), dom.ID(), oldSrcPath, newSrcPath, devAlias, reason))
def myDomainEventTrayChangeCallback(conn, dom, devAlias, reason, opaque):
    print("myDomainEventTrayChangeCallback: Domain %s(%s) tray change devAlias: %s reason: %s" % (
            dom.name(), dom.ID(), devAlias, reason))
def myDomainEventPMWakeupCallback(conn, dom, reason, opaque):
    print("myDomainEventPMWakeupCallback: Domain %s(%s) system pmwakeup" % (
            dom.name(), dom.ID()))
def myDomainEventPMSuspendCallback(conn, dom, reason, opaque):
    print("myDomainEventPMSuspendCallback: Domain %s(%s) system pmsuspend" % (
            dom.name(), dom.ID()))
def myDomainEventBalloonChangeCallback(conn, dom, actual, opaque):
    print("myDomainEventBalloonChangeCallback: Domain %s(%s) %d" % (dom.name(), dom.ID(), actual))
def myDomainEventPMSuspendDiskCallback(conn, dom, reason, opaque):
    print("myDomainEventPMSuspendDiskCallback: Domain %s(%s) system pmsuspend_disk" % (
            dom.name(), dom.ID()))
def myDomainEventDeviceRemovedCallback(conn, dom, dev, opaque):
    print("myDomainEventDeviceRemovedCallback: Domain %s(%s) device removed: %s" % (
            dom.name(), dom.ID(), dev))
def myDomainEventBlockJob2Callback(conn, dom, disk, type, status, opaque):
    print("myDomainEventBlockJob2Callback: Domain %s(%s) %s on disk %s %s" % (dom.name(), dom.ID(), blockJobTypeToString(type), disk, blockJobStatusToString(status)))
def myDomainEventTunableCallback(conn, dom, params, opaque):
    print("myDomainEventTunableCallback: Domain %s(%s) %s" % (dom.name(), dom.ID(), params))
def myDomainEventAgentLifecycleCallback(conn, dom, state, reason, opaque):
    print("myDomainEventAgentLifecycleCallback: Domain %s(%s) %s %s" % (dom.name(), dom.ID(), agentLifecycleStateToString(state), agentLifecycleReasonToString(reason)))
def myDomainEventDeviceAddedCallback(conn, dom, dev, opaque):
    print("myDomainEventDeviceAddedCallback: Domain %s(%s) device added: %s" % (
            dom.name(), dom.ID(), dev))
def myDomainEventMigrationIteration(conn, dom, iteration, opaque):
    print("myDomainEventMigrationIteration: Domain %s(%s) started migration iteration %d" % (
            dom.name(), dom.ID(), iteration))
def myDomainEventJobCompletedCallback(conn, dom, params, opaque):
    print("myDomainEventJobCompletedCallback: Domain %s(%s) %s" % (dom.name(), dom.ID(), params))
def myDomainEventDeviceRemovalFailedCallback(conn, dom, dev, opaque):
    print("myDomainEventDeviceRemovalFailedCallback: Domain %s(%s) failed to remove device: %s" % (
            dom.name(), dom.ID(), dev))
def myDomainEventMetadataChangeCallback(conn, dom, mtype, nsuri, opaque):
    print("myDomainEventMetadataChangeCallback: Domain %s(%s) changed metadata mtype=%d nsuri=%s" % (
            dom.name(), dom.ID(), mtype, nsuri))
def myDomainEventBlockThresholdCallback(conn, dom, dev, path, threshold, excess, opaque):
    print("myDomainEventBlockThresholdCallback: Domain %s(%s) block device %s(%s) threshold %d exceeded by %d" % (
            dom.name(), dom.ID(), dev, path, threshold, excess))

##########################################################################
# Network events
##########################################################################
def netEventToString(event):
    netEventStrings = ( "Defined",
                     "Undefined",
                     "Started",
                     "Stopped",
    )
    return netEventStrings[event]

def netDetailToString(event, detail):
    netEventStrings = (
        ( "Added", ),
        ( "Removed", ),
        ( "Started", ),
        ( "Stopped", ),
    )
    return netEventStrings[event][detail]

def myNetworkEventLifecycleCallback(conn, net, event, detail, opaque):
    print("myNetworkEventLifecycleCallback: Network %s %s %s" % (net.name(),
                                                                 netEventToString(event),
                                                                 netDetailToString(event, detail)))

##########################################################################
# Storage pool events
##########################################################################
def storageEventToString(event):
    storageEventStrings = ( "Defined",
                            "Undefined",
                            "Started",
                            "Stopped",
    )
    return storageEventStrings[event]

def myStoragePoolEventLifecycleCallback(conn, pool, event, detail, opaque):
    print("myStoragePoolEventLifecycleCallback: Storage pool %s %s %d" % (pool.name(),
                                                                          storageEventToString(event),
                                                                          detail))

def myStoragePoolEventRefreshCallback(conn, pool, opaque):
    print("myStoragePoolEventRefreshCallback: Storage pool %s" % pool.name())

##########################################################################
# Node device events
##########################################################################
def nodeDeviceEventToString(event):
    nodeDeviceEventStrings = ( "Created",
                               "Deleted",
    )
    return nodeDeviceEventStrings[event]

def myNodeDeviceEventLifecycleCallback(conn, dev, event, detail, opaque):
    print("myNodeDeviceEventLifecycleCallback: Node device  %s %s %d" % (dev.name(),
                                                                          nodeDeviceEventToString(event),
                                                                          detail))

def myNodeDeviceEventUpdateCallback(conn, dev, opaque):
    print("myNodeDeviceEventUpdateCallback: Node device %s" % dev.name())

##########################################################################
# Secret events
##########################################################################
def secretEventToString(event):
    secretEventStrings = ( "Defined",
                           "Undefined",
    )
    return secretEventStrings[event]

def mySecretEventLifecycleCallback(conn, secret, event, detail, opaque):
    print("mySecretEventLifecycleCallback: Secret %s %s %d" % (secret.UUIDString(),
                                                               secretEventToString(event),
                                                               detail))

def mySecretEventValueChanged(conn, secret, opaque):
    print("mySecretEventValueChanged: Secret %s" % secret.UUIDString())

##########################################################################
# Set up and run the program
##########################################################################

run = True

def myConnectionCloseCallback(conn, reason, opaque):
    reasonStrings = (
        "Error", "End-of-file", "Keepalive", "Client",
        )
    print("myConnectionCloseCallback: %s: %s" % (conn.getURI(), reasonStrings[reason]))
    run = False

def usage():
    print("usage: "+os.path.basename(sys.argv[0])+" [-hdl] [uri]")
    print("   uri will default to qemu:///system")
    print("   --help, -h   Print this help message")
    print("   --debug, -d  Print debug output")
    print("   --loop=TYPE, -l   Choose event-loop-implementation (native, poll, asyncio)")
    print("   --timeout=SECS  Quit after SECS seconds running")

def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hdl:", ["help", "debug", "loop=", "timeout="])
    except getopt.GetoptError as err:
        # print help information and exit:
        print(str(err)) # will print something like "option -a not recognized"
        usage()
        sys.exit(2)
    timeout = None
    for o, a in opts:
        if o in ("-h", "--help"):
            usage()
            sys.exit()
        if o in ("-d", "--debug"):
            global do_debug
            do_debug = True
        if o in ("-l", "--loop"):
            global event_impl
            event_impl = a
        if o in ("--timeout"):
            timeout = int(a)

    if len(args) >= 1:
        uri = args[0]
    else:
        uri = "qemu:///system"

    print("Using uri '%s' and event loop '%s'" % (uri, event_impl))

    # Run a background thread with the event loop
    if event_impl == "poll":
        virEventLoopPollStart()
    elif event_impl == "asyncio":
        virEventLoopAIOStart()
    else:
        virEventLoopNativeStart()

    vc = libvirt.openReadOnly(uri)

    # Close connection on exit (to test cleanup paths)
    old_exitfunc = getattr(sys, 'exitfunc', None)
    def exit():
        print("Closing " + vc.getURI())
        vc.close()
        if (old_exitfunc): old_exitfunc()
    sys.exitfunc = exit

    vc.registerCloseCallback(myConnectionCloseCallback, None)

    #Add 2 lifecycle callbacks to prove this works with more than just one
    vc.domainEventRegister(myDomainEventCallback1,None)
    domcallbacks = []
    domcallbacks.append(vc.domainEventRegisterAny(None, libvirt.VIR_DOMAIN_EVENT_ID_LIFECYCLE, myDomainEventCallback2, None))
    domcallbacks.append(vc.domainEventRegisterAny(None, libvirt.VIR_DOMAIN_EVENT_ID_REBOOT, myDomainEventRebootCallback, None))
    domcallbacks.append(vc.domainEventRegisterAny(None, libvirt.VIR_DOMAIN_EVENT_ID_RTC_CHANGE, myDomainEventRTCChangeCallback, None))
    domcallbacks.append(vc.domainEventRegisterAny(None, libvirt.VIR_DOMAIN_EVENT_ID_WATCHDOG, myDomainEventWatchdogCallback, None))
    domcallbacks.append(vc.domainEventRegisterAny(None, libvirt.VIR_DOMAIN_EVENT_ID_IO_ERROR, myDomainEventIOErrorCallback, None))
    domcallbacks.append(vc.domainEventRegisterAny(None, libvirt.VIR_DOMAIN_EVENT_ID_GRAPHICS, myDomainEventGraphicsCallback, None))
    domcallbacks.append(vc.domainEventRegisterAny(None, libvirt.VIR_DOMAIN_EVENT_ID_IO_ERROR_REASON, myDomainEventIOErrorReasonCallback, None))
    domcallbacks.append(vc.domainEventRegisterAny(None, libvirt.VIR_DOMAIN_EVENT_ID_CONTROL_ERROR, myDomainEventControlErrorCallback, None))
    domcallbacks.append(vc.domainEventRegisterAny(None, libvirt.VIR_DOMAIN_EVENT_ID_BLOCK_JOB, myDomainEventBlockJobCallback, None))
    domcallbacks.append(vc.domainEventRegisterAny(None, libvirt.VIR_DOMAIN_EVENT_ID_DISK_CHANGE, myDomainEventDiskChangeCallback, None))
    domcallbacks.append(vc.domainEventRegisterAny(None, libvirt.VIR_DOMAIN_EVENT_ID_TRAY_CHANGE, myDomainEventTrayChangeCallback, None))
    domcallbacks.append(vc.domainEventRegisterAny(None, libvirt.VIR_DOMAIN_EVENT_ID_PMWAKEUP, myDomainEventPMWakeupCallback, None))
    domcallbacks.append(vc.domainEventRegisterAny(None, libvirt.VIR_DOMAIN_EVENT_ID_PMSUSPEND, myDomainEventPMSuspendCallback, None))
    domcallbacks.append(vc.domainEventRegisterAny(None, libvirt.VIR_DOMAIN_EVENT_ID_BALLOON_CHANGE, myDomainEventBalloonChangeCallback, None))
    domcallbacks.append(vc.domainEventRegisterAny(None, libvirt.VIR_DOMAIN_EVENT_ID_PMSUSPEND_DISK, myDomainEventPMSuspendDiskCallback, None))
    domcallbacks.append(vc.domainEventRegisterAny(None, libvirt.VIR_DOMAIN_EVENT_ID_DEVICE_REMOVED, myDomainEventDeviceRemovedCallback, None))
    domcallbacks.append(vc.domainEventRegisterAny(None, libvirt.VIR_DOMAIN_EVENT_ID_BLOCK_JOB_2, myDomainEventBlockJob2Callback, None))
    domcallbacks.append(vc.domainEventRegisterAny(None, libvirt.VIR_DOMAIN_EVENT_ID_TUNABLE, myDomainEventTunableCallback, None))
    domcallbacks.append(vc.domainEventRegisterAny(None, libvirt.VIR_DOMAIN_EVENT_ID_AGENT_LIFECYCLE, myDomainEventAgentLifecycleCallback, None))
    domcallbacks.append(vc.domainEventRegisterAny(None, libvirt.VIR_DOMAIN_EVENT_ID_DEVICE_ADDED, myDomainEventDeviceAddedCallback, None))
    domcallbacks.append(vc.domainEventRegisterAny(None, libvirt.VIR_DOMAIN_EVENT_ID_MIGRATION_ITERATION, myDomainEventMigrationIteration, None))
    domcallbacks.append(vc.domainEventRegisterAny(None, libvirt.VIR_DOMAIN_EVENT_ID_JOB_COMPLETED, myDomainEventJobCompletedCallback, None))
    domcallbacks.append(vc.domainEventRegisterAny(None, libvirt.VIR_DOMAIN_EVENT_ID_DEVICE_REMOVAL_FAILED, myDomainEventDeviceRemovalFailedCallback, None))
    domcallbacks.append(vc.domainEventRegisterAny(None, libvirt.VIR_DOMAIN_EVENT_ID_METADATA_CHANGE, myDomainEventMetadataChangeCallback, None))
    domcallbacks.append(vc.domainEventRegisterAny(None, libvirt.VIR_DOMAIN_EVENT_ID_BLOCK_THRESHOLD, myDomainEventBlockThresholdCallback, None))

    netcallbacks = []
    netcallbacks.append(vc.networkEventRegisterAny(None, libvirt.VIR_NETWORK_EVENT_ID_LIFECYCLE, myNetworkEventLifecycleCallback, None))

    poolcallbacks = []
    poolcallbacks.append(vc.storagePoolEventRegisterAny(None, libvirt.VIR_STORAGE_POOL_EVENT_ID_LIFECYCLE, myStoragePoolEventLifecycleCallback, None))
    poolcallbacks.append(vc.storagePoolEventRegisterAny(None, libvirt.VIR_STORAGE_POOL_EVENT_ID_REFRESH, myStoragePoolEventRefreshCallback, None))

    devcallbacks = []
    devcallbacks.append(vc.nodeDeviceEventRegisterAny(None, libvirt.VIR_NODE_DEVICE_EVENT_ID_LIFECYCLE, myNodeDeviceEventLifecycleCallback, None))
    devcallbacks.append(vc.nodeDeviceEventRegisterAny(None, libvirt.VIR_NODE_DEVICE_EVENT_ID_UPDATE, myNodeDeviceEventUpdateCallback, None))

    seccallbacks = []
    seccallbacks.append(vc.secretEventRegisterAny(None, libvirt.VIR_SECRET_EVENT_ID_LIFECYCLE, mySecretEventLifecycleCallback, None))
    seccallbacks.append(vc.secretEventRegisterAny(None, libvirt.VIR_SECRET_EVENT_ID_VALUE_CHANGED, mySecretEventValueChanged, None))

    vc.setKeepAlive(5, 3)

    # The rest of your app would go here normally, but for sake
    # of demo we'll just go to sleep. The other option is to
    # run the event loop in your main thread if your app is
    # totally event based.
    count = 0
    while run and (timeout is None or count < timeout):
        count = count + 1
        time.sleep(1)

    vc.domainEventDeregister(myDomainEventCallback1)

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
