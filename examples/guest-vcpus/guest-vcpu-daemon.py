#!/usr/bin/env python3
"""
This service waits for the guest agent lifecycle event and reissues
guest agent calls to modify the cpu count according to the metadata
set by guest-vcpu.py example
"""

import libvirt
import threading
from xml.dom import minidom
import time
from argparse import ArgumentParser

uri = "qemu:///system"
customXMLuri = "guest-cpu.python.libvirt.org"
connectRetryTimeout = 5


class workerData:
    def __init__(self):
        self.doms = list()
        self.conn = None
        self.cond = threading.Condition()

    def notify(self):
        self.cond.acquire()
        self.cond.notify()
        self.cond.release()

    def waitNotify(self):
        self.cond.acquire()
        self.cond.wait()
        self.cond.release()

    def addDomainNotify(self, dom):
        self.doms.append(dom)
        self.notify()

    def closeConnectNotify(self):
        conn = self.conn
        self.conn = None
        conn.close()
        self.notify()

    def setConnect(self, conn):
        self.conn = conn

    def hasConn(self):
        return self.conn is not None

    def hasDom(self):
        return len(self.doms) > 0

    def getDom(self):
        return self.doms.pop()

    def setDoms(self, doms):
        self.doms = doms


def virEventLoopNativeRun():
    while True:
        libvirt.virEventRunDefaultImpl()


def handleAgentLifecycleEvent(conn, dom, state, reason, opaque):
    if state == libvirt.VIR_CONNECT_DOMAIN_EVENT_AGENT_LIFECYCLE_STATE_CONNECTED:
        opaque.addDomainNotify(dom)


def handleConnectClose(conn, reason, opaque):
    print('Disconnected from ' + uri)
    opaque.closeConnectNotify()


def handleLibvirtLibraryError(opaque, error):
    pass


def processAgentConnect(dom):
    try:
        cpus = dom.metadata(libvirt.VIR_DOMAIN_METADATA_ELEMENT, customXMLuri, libvirt.VIR_DOMAIN_AFFECT_LIVE)
        doc = minidom.parseString(cpus)
        ncpus = int(doc.getElementsByTagName('ncpus')[0].getAttribute('count'))
    except Exception:
        return

    try:
        dom.setVcpusFlags(ncpus, libvirt.VIR_DOMAIN_AFFECT_LIVE | libvirt.VIR_DOMAIN_VCPU_GUEST)
        print("set vcpu count for domain " + dom.name() + " to " + str(ncpus))
    except Exception:
        print("failed to set vcpu count for domain " + dom.name())


def work():
    data = workerData()

    print("Using uri: " + uri)

    while True:
        if not data.hasConn():
            try:
                conn = libvirt.open(uri)
            except libvirt.libvirtError:
                print('Failed to connect to ' + uri + ', retry in ' + str(connectRetryTimeout)) + ' seconds'
                time.sleep(connectRetryTimeout)
                continue

            print('Connected to ' + uri)

            data.setConnect(conn)
            conn.registerCloseCallback(handleConnectClose, data)
            conn.setKeepAlive(5, 3)
            conn.domainEventRegisterAny(None,
                                        libvirt.VIR_DOMAIN_EVENT_ID_AGENT_LIFECYCLE,
                                        handleAgentLifecycleEvent,
                                        data)

            data.setDoms(conn.listAllDomains(libvirt.VIR_CONNECT_LIST_DOMAINS_ACTIVE))

        while data.hasConn() and data.hasDom():
            processAgentConnect(data.getDom())

        data.waitNotify()


def main():
    libvirt.virEventRegisterDefaultImpl()
    libvirt.registerErrorHandler(handleLibvirtLibraryError, None)

    worker = threading.Thread(target=work)
    worker.setDaemon(True)
    worker.start()

    eventLoop = threading.Thread(target=virEventLoopNativeRun)
    eventLoop.setDaemon(True)
    eventLoop.start()

    while True:
        time.sleep(1)


if __name__ == "__main__":
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("uri", nargs="?", default=uri)
    args = parser.parse_args()

    uri = args.uri

    main()
