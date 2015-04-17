#!/usr/bin/env python

import libvirt
import sys
import getopt
import os

customXMLuri = "guest-cpu.python.libvirt.org"

def usage():
    print("usage: "+os.path.basename(sys.argv[0])+" [-hcl] domain count [uri]")
    print("   uri will default to qemu:///system")
    print("   --help, -h   Print(this help message")
    print("   --config, -c Modify persistent domain configuration")
    print("   --live, -l   Modify live domain configuration")
    print("")
    print("Sets the vCPU count via the guest agent and sets the metadata element " +
           "used by guest-vcpu-daemon.py example")

uri = "qemu:///system"
flags = 0
live = False;
config = False;

try:
    opts, args = getopt.getopt(sys.argv[1:], "hcl", ["help", "config", "live"])
except getopt.GetoptError as err:
    # print help information and exit:
    print(str(err)) # will print something like "option -a not recognized"
    usage()
    sys.exit(2)
for o, a in opts:
    if o in ("-h", "--help"):
        usage()
        sys.exit()
    if o in ("-c", "--config"):
        config = True
        flags |= libvirt.VIR_DOMAIN_AFFECT_CONFIG
    if o in ("-l", "--live"):
        live = True
        flags |= libvirt.VIR_DOMAIN_AFFECT_LIVE

if len(args) < 2:
    usage()
    sys.exit(1)
elif len(args) >= 3:
    uri = args[2]

domain = args[0]
count = int(args[1])

conn = libvirt.open(uri)
dom = conn.lookupByName(domain)

if flags == 0 or config:
    confvcpus = dom.vcpusFlags(libvirt.VIR_DOMAIN_AFFECT_CONFIG)

    if confvcpus < count:
        print("Persistent domain configuration has only " + str(confvcpus) + " vcpus configured")
        sys.exit(1)

if flags == 0 or live:
    livevcpus = dom.vcpusFlags(libvirt.VIR_DOMAIN_AFFECT_LIVE)

    if livevcpus < count:
        print("Live domain configuration has only " + str(livevcpus) + " vcpus configured")
        sys.exit(1)

if flags == 0 or live:
    dom.setVcpusFlags(count, libvirt.VIR_DOMAIN_AFFECT_LIVE | libvirt.VIR_DOMAIN_VCPU_GUEST)

meta = "<ncpus count='" + str(count) + "'/>"

dom.setMetadata(libvirt.VIR_DOMAIN_METADATA_ELEMENT, meta, "guestvcpudaemon", customXMLuri, flags)
