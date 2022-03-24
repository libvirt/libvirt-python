from typing import Any, Callable, Dict, List, IO


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

def qemuMonitorCommandWithFiles(domain: libvirt.virDomain, cmd: str, files: List[int] = [], flags: int = 0) -> (str, List[IO]):
    """This API is QEMU specific, so it will only work with hypervisor
    connections to the QEMU driver with local connections using the unix
    socket.

    Send an arbitrary monitor command @cmd with file descriptors @files to
    domain through the QEMU monitor and optionally return a list of files
    in the returned tuple. There are several requirements to safely
    and successfully use this API:

   - A @cmd that queries state without making any modifications is safe
   - A @cmd that alters state that is also tracked by libvirt is unsafe,
     and may cause libvirtd to crash
   - A @cmd that alters state not tracked by the current version of
     libvirt is possible as a means to test new qemu features before
     they have support in libvirt, but no guarantees are made to safety

    If VIR_DOMAIN_QEMU_MONITOR_COMMAND_HMP is set, the command is considered to
    be a human monitor command and libvirt will automatically convert it into
    QMP if needed.  In that case the @result will also be converted back from
    QMP.

    Returns a tuple consisting of the string output from @cmd and a list of
    files respectively."""
    ret = libvirtmod_qemu.virDomainQemuMonitorCommandWithFiles(domain._o, cmd, files, flags)
    if ret is None:
        raise libvirt.libvirtError('virDomainQemuMonitorCommandWithFiles() failed')
    return ret
