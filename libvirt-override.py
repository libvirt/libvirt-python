#
# Manually written part of python bindings for libvirt
#

# On cygwin, the DLL is called cygvirtmod.dll
try:
    import libvirtmod  # type: ignore
except ImportError as lib_e:
    try:
        import cygvirtmod as libvirtmod  # type: ignore
    except ImportError as cyg_e:
        if "No module named" in str(cyg_e):
            raise lib_e

from types import TracebackType
from typing import Any, Callable, Dict, List, Optional, overload, Tuple, Type, TypeVar, Union
_T = TypeVar('_T')
_EventCB = Callable[[int, int, int, _T], None]
_EventAddHandleFunc = Callable[[int, int, _EventCB, _T], int]
_EventUpdateHandleFunc = Callable[[int, int], None]
_EventRemoveHandleFunc = Callable[[int], int]
_TimerCB = Callable[[int, _T], None]
_EventAddTimeoutFunc = Callable[[int, _TimerCB, _T], int]
_EventUpdateTimeoutFunc = Callable[[int, int], None]
_EventRemoveTimeoutFunc = Callable[[int], int]
_DomainCB = Callable[['virConnect', 'virDomain', int, int, _T], Optional[int]]
_BlkioParameter = Dict[str, Any]
_MemoryParameter = Dict[str, Any]
_SchedParameter = Dict[str, Any]
_TypedParameter = Dict[str, Any]


# The root of all libvirt errors.
class libvirtError(Exception):
    def __init__(self, defmsg: str) -> None:

        # Never call virConnGetLastError().
        # virGetLastError() is now thread local
        err = libvirtmod.virGetLastError()  # type: Optional[Tuple[int, int, str, int, str, Optional[str], Optional[str], int, int]]
        if err is None:
            msg = defmsg
        else:
            msg = err[2]

        Exception.__init__(self, msg)

        self.err = err

    def get_error_code(self) -> Optional[int]:
        if self.err is None:
            return None
        return self.err[0]

    def get_error_domain(self) -> Optional[int]:
        if self.err is None:
            return None
        return self.err[1]

    def get_error_message(self) -> Optional[str]:
        if self.err is None:
            return None
        return self.err[2]

    def get_error_level(self) -> Optional[int]:
        if self.err is None:
            return None
        return self.err[3]

    def get_str1(self) -> Optional[str]:
        if self.err is None:
            return None
        return self.err[4]

    def get_str2(self) -> Optional[str]:
        if self.err is None:
            return None
        return self.err[5]

    def get_str3(self) -> Optional[str]:
        if self.err is None:
            return None
        return self.err[6]

    def get_int1(self) -> Optional[int]:
        if self.err is None:
            return None
        return self.err[7]

    def get_int2(self) -> Optional[int]:
        if self.err is None:
            return None
        return self.err[8]


#
# register the libvirt global error handler
#
def registerErrorHandler(f: Callable[[_T, List], None], ctx: _T) -> int:
    """Register a Python function for error reporting.
       The function is called back as f(ctx, error), with error
       being a list of information about the error being raised.
       Returns 1 in case of success."""
    return libvirtmod.virRegisterErrorHandler(f, ctx)


def openAuth(uri: str, auth: List, flags: int = 0) -> 'virConnect':
    # TODO: The C code rquires a List and there is not *Mutable*Tuple for a better description such as
    # auth: Tuple[List[int], Callable[[List[MutableTuple[int, str, str, str, Any]], _T], int], _T]
    """
    This function should be called first to get a connection to the
    Hypervisor. If necessary, authentication will be performed fetching
    credentials via the callback.

    See :py:func:`open` for notes about environment variables which can
    have an effect on opening drivers and freeing the connection resources.

    :param str uri: (Optional) connection URI, see https://libvirt.org/uri.html
    :param auth: a list that contains 3 items:
        - a list of supported credential types
        - a callable that takes 2 arguments (credentials, user-data) and returns 0 on succcess and -1 on errors.
            The credentials argument is a list of credentials that libvirt (actually
            the ESX driver) would like to request. An element of this list is itself a
            list containing 5 items (4 inputs, 1 output):
                - the credential type, e.g. :py:const:`libvirt.VIR_CRED_AUTHNAME`
                - a prompt to be displayed to the user
                - a challenge, the ESX driver sets this to the hostname to allow automatic
                    distinction between requests for ESX and vCenter credentials
                - a default result for the request
                - a place to store the actual result for the request
        - user data that will be passed to the callable as second argument
    :param int flags: bitwise-OR of virConnectFlags
    :returns: a :py:class:`virConnect` instance on success.
    :raises libvirtError: on errors.
    """
    ret = libvirtmod.virConnectOpenAuth(uri, auth, flags)
    if ret is None:
        raise libvirtError('virConnectOpenAuth() failed')
    return virConnect(_obj=ret)


#
# Return library version.
#
def getVersion(name: Optional[str] = None) -> int:
    """If no name parameter is passed (or name is None) then the
    version of the libvirt library is returned as an integer.

    If a name is passed and it refers to a driver linked to the
    libvirt library, then this returns a tuple of (library version,
    driver version).

    If the name passed refers to a non-existent driver, then you
    will get the exception 'no support for hypervisor'.

    Versions numbers are integers: 1000000*major + 1000*minor + release."""
    if name is None:
        ret = libvirtmod.virGetVersion()
    else:
        ret = libvirtmod.virGetVersion(name)
    if ret is None:
        raise libvirtError("virGetVersion() failed")
    return ret


#
# Invoke an EventHandle callback
#
@overload
def _eventInvokeHandleCallback(watch: int, fd: int, event: int, opaque: Tuple[_EventCB, _T], opaquecompat: None = None) -> None: ...  # noqa E704
@overload  # noqa F811
def _eventInvokeHandleCallback(watch: int, fd: int, event: int, opaque: _EventCB, opaquecompat: _T = None) -> None: ...  # noqa E704
def _eventInvokeHandleCallback(watch: int, fd: int, event: int, opaque: Union[Tuple[_EventCB, _T], _EventCB], opaquecompat: Optional[_T] = None) -> None:  # noqa F811
    """
    Invoke the Event Impl Handle Callback in C
    """
    # libvirt 0.9.2 and earlier required custom event loops to know
    # that opaque=(cb, original_opaque) and pass the values individually
    # to this wrapper. This should handle the back compat case, and make
    # future invocations match the virEventHandleCallback prototype
    if opaquecompat:
        callback = opaque
        opaque_ = opaquecompat
    else:
        assert isinstance(opaque, tuple)
        callback = opaque[0]
        opaque_ = opaque[1]

    libvirtmod.virEventInvokeHandleCallback(watch, fd, event, callback, opaque_)


#
# Invoke an EventTimeout callback
#
def _eventInvokeTimeoutCallback(timer: int, opaque: Union[Tuple[_TimerCB, _T], _TimerCB], opaquecompat: Optional[_T] = None) -> None:
    """
    Invoke the Event Impl Timeout Callback in C
    """
    # libvirt 0.9.2 and earlier required custom event loops to know
    # that opaque=(cb, original_opaque) and pass the values individually
    # to this wrapper. This should handle the back compat case, and make
    # future invocations match the virEventTimeoutCallback prototype
    if opaquecompat:
        callback = opaque
        opaque_ = opaquecompat
    else:
        assert isinstance(opaque, tuple)
        callback = opaque[0]
        opaque_ = opaque[1]

    libvirtmod.virEventInvokeTimeoutCallback(timer, callback, opaque_)


def _dispatchEventHandleCallback(watch: int, fd: int, events: int, cbData: Dict[str, Any]) -> int:
    cb = cbData["cb"]
    opaque = cbData["opaque"]

    cb(watch, fd, events, opaque)
    return 0


def _dispatchEventTimeoutCallback(timer: int, cbData: Dict[str, Any]) -> int:
    cb = cbData["cb"]
    opaque = cbData["opaque"]

    cb(timer, opaque)
    return 0


def virEventAddHandle(fd: int, events: int, cb: _EventCB, opaque: _T) -> int:
    """
    register a callback for monitoring file handle events

    @fd: file handle to monitor for events
    @events: bitset of events to watch from virEventHandleType constants
    @cb: callback to invoke when an event occurs
    @opaque: user data to pass to callback

    Example callback prototype is:
        def cb(watch,   # int id of the handle
               fd,      # int file descriptor the event occurred on
               events,  # int bitmap of events that have occurred
               opaque): # opaque data passed to eventAddHandle
    """
    cbData = {"cb": cb, "opaque": opaque}
    ret = libvirtmod.virEventAddHandle(fd, events, cbData)
    if ret == -1:
        raise libvirtError('virEventAddHandle() failed')
    return ret


def virEventAddTimeout(timeout: int, cb: _TimerCB, opaque: _T) -> int:
    """
    register a callback for a timer event

    @timeout: time between events in milliseconds
    @cb: callback to invoke when an event occurs
    @opaque: user data to pass to callback

    Setting timeout to -1 will disable the timer. Setting the timeout
    to zero will cause it to fire on every event loop iteration.

    Example callback prototype is:
        def cb(timer,   # int id of the timer
               opaque): # opaque data passed to eventAddTimeout
    """
    cbData = {"cb": cb, "opaque": opaque}
    ret = libvirtmod.virEventAddTimeout(timeout, cbData)
    if ret == -1:
        raise libvirtError('virEventAddTimeout() failed')
    return ret


#
# a caller for the ff callbacks for custom event loop implementations
#

def virEventInvokeFreeCallback(opaque: Any) -> None:
    """
    Execute callback which frees the opaque buffer

    @opaque: the opaque object passed to addHandle or addTimeout

    WARNING: This function should not be called from any call by libvirt's
    core. It will most probably cause deadlock in C-level libvirt code.
    Instead it should be scheduled and called from implementation's stack.

    See https://libvirt.org/html/libvirt-libvirt-event.html#virEventAddHandleFunc
    for more information.

    This function is not dependent on any event loop implementation.
    """

    libvirtmod.virEventInvokeFreeCallback(opaque[2], opaque[1])
