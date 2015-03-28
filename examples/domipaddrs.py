#!/usr/bin/env python
# domipaddrs - print domain interfaces along with their MAC and IP addresses

import libvirt
import sys

def usage():
    print "Usage: %s [URI] DOMAIN" % sys.argv[0]
    print "        Print domain interfaces along with their MAC and IP addresses"

uri = None
name = None
args = len(sys.argv)

if args == 2:
    name = sys.argv[1]
elif args == 3:
    uri = sys.argv[1]
    name = sys.argv[2]
else:
    usage()
    sys.exit(2)

conn = libvirt.open(uri)
if conn == None:
    print "Unable to open connection to libvirt"
    sys.exit(1)

try:
    dom = conn.lookupByName(name)
except libvirt.libvirtError:
    print "Domain %s not found" % name
    sys.exit(0)

ifaces = dom.interfaceAddresses(libvirt.VIR_DOMAIN_INTERFACE_ADDRESSES_SRC_LEASE);
if (ifaces == None):
    print "Failed to get domain interfaces"
    sys.exit(0)

print " {0:10} {1:20} {2:12} {3}".format("Interface", "MAC address", "Protocol", "Address")

def toIPAddrType(addrType):
    if addrType == libvirt.VIR_IP_ADDR_TYPE_IPV4:
        return "ipv4"
    elif addrType == libvirt.VIR_IP_ADDR_TYPE_IPV6:
        return "ipv6"

for (name, val) in ifaces.iteritems():
    if val['addrs']:
        for addr in val['addrs']:
           print " {0:10} {1:19}".format(name, val['hwaddr']),
           print " {0:12} {1}/{2} ".format(toIPAddrType(addr['type']), addr['addr'], addr['prefix']),
           print
    else:
        print " {0:10} {1:19}".format(name, val['hwaddr']),
        print " {0:12} {1}".format("N/A", "N/A"),
        print
