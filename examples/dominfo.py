#!/usr/bin/env python3
# dominfo - print some information about a domain

import libvirt
import sys
import libxml2

def usage() -> None:
    print('Usage: %s DOMAIN' % sys.argv[0])
    print('       Print information about the domain DOMAIN')

def print_section(title: str) -> None:
    print("\n%s" % title)
    print("=" * 60)

def print_entry(key: str, value: str) -> None:
    print("%-10s %-10s" % (key, value))

def print_xml(key: str, ctx, path: str) -> str:
    res = ctx.xpathEval(path)
    if res is None or len(res) == 0:
        value = "Unknown"
    else:
        value = res[0].content
    print_entry(key, value)
    return value

if len(sys.argv) != 2:
    usage()
    sys.exit(2)

name = sys.argv[1]

# Connect to libvirt
try:
    conn = libvirt.openReadOnly(None)
except libvirt.libvirtError:
    print('Failed to open connection to the hypervisor')
    sys.exit(1)

try:
    dom = conn.lookupByName(name)
    # Annoyiingly, libvirt prints its own error message here
except libvirt.libvirtError:
    print("Domain %s is not running" % name)
    sys.exit(0)

info = dom.info()
print_section("Domain info")
print_entry("State:", info[0])
print_entry("MaxMem:", info[1])
print_entry("UsedMem:", info[2])
print_entry("VCPUs:", info[3])

# Read some info from the XML desc
xmldesc = dom.XMLDesc(0)
doc = libxml2.parseDoc(xmldesc)
ctx = doc.xpathNewContext()
print_section("Kernel")
print_xml("Type:", ctx, "/domain/os/type")
print_xml("Kernel:", ctx, "/domain/os/kernel")
print_xml("initrd:", ctx, "/domain/os/initrd")
print_xml("cmdline:", ctx, "/domain/os/cmdline")

print_section("Devices")
devs = ctx.xpathEval("/domain/devices/*")
for d in devs:
    ctx.setContextNode(d)
    # import pdb; pdb.set_trace()
    type = print_xml("Type:", ctx, "@type")
    if type == "file":
        print_xml("Source:", ctx, "source/@file")
        print_xml("Target:", ctx, "target/@dev")
    elif type == "block":
        print_xml("Source:", ctx, "source/@dev")
        print_xml("Target:", ctx, "target/@dev")
    elif type == "bridge":
        print_xml("Source:", ctx, "source/@bridge")
        print_xml("MAC Addr:", ctx, "mac/@address")
