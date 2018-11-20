# Manually written part of python bindings for libvirt-qemu
from typing import Any, Callable, Dict


def _dispatchQemuMonitorEventCallback(conn: libvirt.virConnect, dom: libvirt.virDomain, event: str, seconds: int, micros: int, details: str, cbData: Dict[str, Any]) -> int:
    """Dispatches events to python user qemu monitor event callbacks
    """
    cb = cbData["cb"]
    opaque = cbData["opaque"]

    cb(conn, libvirt.virDomain(conn, _obj=dom), event, seconds, micros, details, opaque)
    return 0


def qemuMonitorEventDeregister(conn: libvirt.virConnect, callbackID: int) -> None:
    """Removes a qemu monitor event callback. De-registering for a callback
       will disable delivery of this event type"""
    try:
        ret = libvirtmod_qemu.virConnectDomainQemuMonitorEventDeregister(conn._o, callbackID)
        if ret == -1:
            raise libvirt.libvirtError('virConnectDomainQemuMonitorEventDeregister() failed')
        del conn.qemuMonitorEventCallbackID[callbackID]  # type: ignore
    except AttributeError:
        pass


def qemuMonitorEventRegister(conn: libvirt.virConnect, dom: libvirt.virDomain, event: str, cb: Callable[[libvirt.virConnect, libvirt.virDomain, str, int, int, str, libvirt._T], None], opaque: libvirt._T, flags: int = 0) -> int:
    """Adds a qemu monitor event callback. Registering for a monitor
       callback will enable delivery of the events"""
    if not hasattr(conn, 'qemuMonitorEventCallbackID'):
        conn.qemuMonitorEventCallbackID = {}  # type: ignore
    cbData = {"cb": cb, "conn": conn, "opaque": opaque}
    if dom is None:
        ret = libvirtmod_qemu.virConnectDomainQemuMonitorEventRegister(conn._o, None, event, cbData, flags)
    else:
        ret = libvirtmod_qemu.virConnectDomainQemuMonitorEventRegister(conn._o, dom._o, event, cbData, flags)
    if ret == -1:
        raise libvirt.libvirtError('virConnectDomainQemuMonitorEventRegister() failed')
    conn.qemuMonitorEventCallbackID[ret] = opaque  # type: ignore
    return ret
