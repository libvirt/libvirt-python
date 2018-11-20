#!/usr/bin/env python3
"""
Print domain interfaces along with their MAC and IP addresses
"""

import libvirt
from argparse import ArgumentParser

IPTYPE = {
    libvirt.VIR_IP_ADDR_TYPE_IPV4: "ipv4",
    libvirt.VIR_IP_ADDR_TYPE_IPV6: "ipv6",
}


def print_dom_ifaces(dom: libvirt.virDomain) -> None:
    ifaces = dom.interfaceAddresses(libvirt.VIR_DOMAIN_INTERFACE_ADDRESSES_SRC_LEASE)
    if ifaces is None:
        print("Failed to get domain interfaces")
        exit(0)

    print(" {0:10} {1:20} {2:12} {3}".format(
        "Interface", "MAC address", "Protocol", "Address"))

    for (name, val) in ifaces.items():
        if val['addrs']:
            for addr in val['addrs']:
                print(" {0:10} {1:19} {2:12} {3}/{4}".format(
                    name,
                    val['hwaddr'],
                    IPTYPE[addr['type']],
                    addr['addr'],
                    addr['prefix']))
        else:
            print(" {0:10} {1:19} {2:12} {3}".format(name, val['hwaddr'], "N/A", "N/A"))


if __name__ == "__main__":
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("uri", nargs="?", default=None)
    parser.add_argument("domain")
    args = parser.parse_args()

    try:
        conn = libvirt.open(args.uri)
    except libvirt.libvirtError:
        raise SystemExit("Unable to open connection to libvirt")

    try:
        dom = conn.lookupByName(args.domain)
    except libvirt.libvirtError:
        print("Domain %s not found" % args.domain)
        exit(0)

    print_dom_ifaces(dom)
    conn.close()
