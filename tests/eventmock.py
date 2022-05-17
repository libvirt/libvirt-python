
import libvirt
import libvirtmod

_add_handle_impl = None
_update_handle_impl = None
_remove_handle_impl = None

_add_timeout_impl = None
_update_timeout_impl = None
_remove_timeout_impl = None

_registered = False

def _add_handle(fd: int, event: int, cb: libvirt._EventCB, opaque: libvirt._T) -> int:
    global _add_handle_impl
    assert _add_handle_impl != None
    return _add_handle_impl(fd, event, cb, opaque)

def _update_handle(watch: int, event: int) -> None:
    global _update_handle_impl
    assert _update_handle_impl != None
    _update_handle_impl(watch, event)

def _remove_handle(watch: int) -> int:
    global _remove_handle_impl
    assert _remove_handle_impl != None
    return _remove_handle_impl(watch)

def _add_timeout(timeout: int, cb: libvirt._TimerCB, opaque: libvirt._T) -> int:
    global _add_timeout_impl
    assert _add_timeout_impl != None
    return _add_timeout_impl(timeout, cb, opaque)

def _update_timeout(timer: int, timeout: int) -> None:
    global _update_timeout_impl
    assert _update_timeout_impl != None
    _update_timeout_impl(timer, timeout)

def _remove_timeout(timer: int) -> int:
    global _remove_timeout_impl
    assert _remove_timeout_impl != None
    return _remove_timeout_impl(timer)

# libvirt.virEventRegisterImpl() is a one time call per process
# This method is intended to be used with mock patching, so that
# tests can get the appearance of being able to call
# virEventRegisterImpl many times.
#
# Note, this relies on the tests closing all connection objects
# and not leaving any handles/timers pending when they stop
# running their event loop impl.

def virEventRegisterImplMock(add_handle_impl,
                             update_handle_impl,
                             remove_handle_impl,
                             add_timeout_impl,
                             update_timeout_impl,
                             remove_timeout_impl):
    global _add_handle_impl
    global _update_handle_impl
    global _remove_handle_impl
    global _add_timeout_impl
    global _update_timeout_impl
    global _remove_timeout_impl

    _add_handle_impl = add_handle_impl
    _update_handle_impl = update_handle_impl
    _remove_handle_impl = remove_handle_impl
    _add_timeout_impl = add_timeout_impl
    _update_timeout_impl = update_timeout_impl
    _remove_timeout_impl = remove_timeout_impl

    global _registered
    if not _registered:
        libvirtmod.virEventRegisterImpl(_add_handle,
                                        _update_handle,
                                        _remove_timeout,
                                        _add_timeout,
                                        _update_timeout,
                                        _remove_timeout)
        _registered = True
