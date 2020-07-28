#!/usr/bin/env python3
"""
Sets the vCPU count via the guest agent and sets the metadata element
used by guest-vcpu-daemon.py example
"""

import libvirt
from argparse import ArgumentParser

customXMLuri = "guest-cpu.python.libvirt.org"

parser = ArgumentParser(description=__doc__)
parser.add_argument("--config", "-c", action="store_true", help="Modify persistent domain configuration")
parser.add_argument("--live", "-l", action="store_true", help="Modify live domain configuration")
parser.add_argument("domain")
parser.add_argument("count", type=int)
parser.add_argument("uri", nargs="?", default="qemu:///system")
args = parser.parse_args()

flags = (libvirt.VIR_DOMAIN_AFFECT_CONFIG if args.config else 0) | (libvirt.VIR_DOMAIN_AFFECT_LIVE if args.live else 0)

conn = libvirt.open(args.uri)
dom = conn.lookupByName(args.domain)

if flags == 0 or args.config:
    confvcpus = dom.vcpusFlags(libvirt.VIR_DOMAIN_AFFECT_CONFIG)

    if confvcpus < args.count:
        print("Persistent domain configuration has only " + str(confvcpus) + " vcpus configured")
        exit(1)

if flags == 0 or args.live:
    livevcpus = dom.vcpusFlags(libvirt.VIR_DOMAIN_AFFECT_LIVE)

    if livevcpus < args.count:
        print("Live domain configuration has only " + str(livevcpus) + " vcpus configured")
        exit(1)

if flags == 0 or args.live:
    dom.setVcpusFlags(args.count, libvirt.VIR_DOMAIN_AFFECT_LIVE | libvirt.VIR_DOMAIN_VCPU_GUEST)

meta = "<ncpus count='" + str(args.count) + "'/>"

dom.setMetadata(libvirt.VIR_DOMAIN_METADATA_ELEMENT, meta, "guestvcpudaemon", customXMLuri, flags)
