#!/usr/bin/env python3
"""
Print leases info for a given virtual network
"""

import libvirt
import time
from argparse import ArgumentParser


parser = ArgumentParser(description=__doc__)
parser.add_argument("uri", nargs="?", default=None)
parser.add_argument("network")
args = parser.parse_args()

try:
    conn = libvirt.open(args.uri)
except libvirt.libvirtError:
    print("Unable to open connection to libvirt")
    exit(1)

try:
    net = conn.networkLookupByName(args.network)
except libvirt.libvirtError:
    print("Network %s not found" % args.network)
    exit(0)

leases = net.DHCPLeases()
if not leases:
    print("Failed to get leases for %s" % net.name())
    exit(0)


def toIPAddrType(addrType: int) -> str:
    if addrType == libvirt.VIR_IP_ADDR_TYPE_IPV4:
        return "ipv4"
    elif addrType == libvirt.VIR_IP_ADDR_TYPE_IPV6:
        return "ipv6"
    return "Unknown"


print(" {0:20} {1:18} {2:9} {3:25} {4:15} {5}".format("Expiry Time",
                                                      "MAC address",
                                                      "Protocol",
                                                      "IP address",
                                                      "Hostname",
                                                      "Client ID or DUID"))
print("-" * 115)

for lease in leases:
    print(" {0:20} {1:18} {2:9} {3:25} {4:15} {5}".format(
        time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(lease['expirytime'])),
        lease['mac'],
        toIPAddrType(lease['type']),
        "{}/{}".format(lease['ipaddr'], lease['prefix']),
        lease['hostname'],
        lease['clientid']
    ))
