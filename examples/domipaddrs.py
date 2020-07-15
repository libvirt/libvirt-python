#!/usr/bin/env python3
# domipaddrs - print domain interfaces along with their MAC and IP addresses

import libvirt
import sys

IPTYPE = {
    libvirt.VIR_IP_ADDR_TYPE_IPV4: "ipv4",
    libvirt.VIR_IP_ADDR_TYPE_IPV6: "ipv6",
}


def print_dom_ifaces(dom):
    ifaces = dom.interfaceAddresses(libvirt.VIR_DOMAIN_INTERFACE_ADDRESSES_SRC_LEASE)
    if (ifaces == None):
        print("Failed to get domain interfaces")
        sys.exit(0)

    print(" {0:10} {1:20} {2:12} {3}".format(
        "Interface", "MAC address", "Protocol", "Address"))

    for (name, val) in ifaces.items():
        if val['addrs']:
            for addr in val['addrs']:
                print (" {0:10} {1:19} {2:12} {3}/{4}".format(
                    name,
                    val['hwaddr'],
                    IPTYPE[addr['type']],
                    addr['addr'],
                    addr['prefix']))
        else:
            print(" {0:10} {1:19} {2:12} {3}".format(name, val['hwaddr'], "N/A", "N/A"))


if __name__ == "__main__":
    uri = None
    name = None
    args = len(sys.argv)

    if args == 2:
        name = sys.argv[1]
    elif args == 3:
        uri = sys.argv[1]
        name = sys.argv[2]
    else:
        print("Usage: %s [URI] DOMAIN" % sys.argv[0])
        print("        Print domain interfaces along with their MAC and IP addresses")
        sys.exit(2)

    try:
        conn = libvirt.open(uri)
    except libvirt.libvirtError:
        raise SystemExit("Unable to open connection to libvirt")

    try:
        dom = conn.lookupByName(name)
    except libvirt.libvirtError:
        print("Domain %s not found" % name)
        sys.exit(0)

    print_dom_ifaces(dom)
    conn.close()
