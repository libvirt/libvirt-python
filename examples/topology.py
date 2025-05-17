#!/usr/bin/env python3
# Parse topology information from the capabilities XML and use
# them to calculate host topology
#
# Authors:
#   Amador Pahim <apahim@redhat.com>
#   Peter Krempa <pkrempa@redhat.com>

import libvirt
from xml.dom import minidom

try:
    conn = libvirt.openReadOnly(None)
except libvirt.libvirtError:
    print('Failed to connect to the hypervisor')
    exit(1)

try:
    capsXML = conn.getCapabilities()
except libvirt.libvirtError:
    print('Failed to request capabilities')
    exit(1)

caps = minidom.parseString(capsXML)
host = caps.getElementsByTagName('host')[0]
cells = host.getElementsByTagName('cells')[0]
total_cpus = cells.getElementsByTagName('cpu').length

socketIds = {
    proc.getAttribute('socket_id')
    for proc in cells.getElementsByTagName('cpu')
}

siblingsIds = {
    proc.getAttribute('siblings')
    for proc in cells.getElementsByTagName('cpu')
}

print("Host topology")
print("NUMA nodes:", cells.getAttribute('num'))
print("   Sockets:", len(socketIds))
print("     Cores:", len(siblingsIds))
print("   Threads:", total_cpus)
