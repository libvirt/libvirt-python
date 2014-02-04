# Manually written part of python bindings for libvirt-qemu

def _dispatchQemuMonitorEventCallback(conn, dom, event, seconds, micros, details, cbData):
    """Dispatches events to python user qemu monitor event callbacks
    """
    cb = cbData["cb"]
    opaque = cbData["opaque"]

    cb(conn, libvirt.virDomain(conn, _obj=dom), event, seconds, micros, details, opaque)
    return 0

def qemuMonitorEventDeregister(conn, callbackID):
    """Removes a qemu monitor event callback. De-registering for a callback
       will disable delivery of this event type"""
    try:
        ret = libvirtmod_qemu.virConnectDomainQemuMonitorEventDeregister(conn._o, callbackID)
        if ret == -1: raise libvirt.libvirtError ('virConnectDomainQemuMonitorEventDeregister() failed')
        del conn.qemuMonitorEventCallbackID[callbackID]
    except AttributeError:
        pass

def qemuMonitorEventRegister(conn, dom, event, cb, opaque, flags=0):
    """Adds a qemu monitor event callback. Registering for a monitor
       callback will enable delivery of the events"""
    if not hasattr(conn, 'qemuMonitorEventCallbackID'):
        conn.qemuMonitorEventCallbackID = {}
    cbData = { "cb": cb, "conn": conn, "opaque": opaque }
    if dom is None:
        ret = libvirtmod_qemu.virConnectDomainQemuMonitorEventRegister(conn._o, None, event, cbData, flags)
    else:
        ret = libvirtmod_qemu.virConnectDomainQemuMonitorEventRegister(conn._o, dom._o, event, cbData, flags)
    if ret == -1:
        raise libvirt.libvirtError ('virConnectDomainQemuMonitorEventRegister() failed')
    conn.qemuMonitorEventCallbackID[ret] = opaque
    return ret
