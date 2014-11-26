#!/usr/bin/env python
# netdhcpleases - print leases info for given virtual network

import libvirt
import sys
import time

def usage():
    print("Usage: %s [URI] NETWORK" % sys.argv[0])
    print("        Print leases info for a given virtual network")

uri = None
network = None
args = len(sys.argv)

if args == 2:
    network = sys.argv[1]
elif args == 3:
    uri = sys.argv[1]
    network = sys.argv[2]
else:
    usage()
    sys.exit(2)

conn = libvirt.open(uri)
if conn == None:
    print("Unable to open connection to libvirt")
    sys.exit(1)

try:
    net = conn.networkLookupByName(network)
except libvirt.libvirtError:
    print("Network %s not found" % network)
    sys.exit(0)

leases = net.DHCPLeases();
if (leases == None):
    print("Failed to get leases for %s" % net.name())
    sys.exit(0)

def toIPAddrType(addrType):
    if addrType == libvirt.VIR_IP_ADDR_TYPE_IPV4:
        return "ipv4"
    elif addrType == libvirt.VIR_IP_ADDR_TYPE_IPV6:
        return "ipv6"

print(" {0:20} {1:18} {2:9} {3:25} {4:15} {5}".format("Expiry Time",
                                                      "MAC address",
                                                      "Protocol",
                                                      "IP address",
                                                      "Hostname",
                                                      "Client ID or DUID"))
print("-"*115)

for lease in leases:
    print(" {0:20} {1:18} {2:9} {3:25} {4:15} {5}".format(
        time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(lease['expirytime'])),
        lease['mac'],
        toIPAddrType(lease['type']),
        "{}/{}".format(lease['ipaddr'], lease['prefix']),
        lease['hostname'],
        lease['clientid']
    ))
