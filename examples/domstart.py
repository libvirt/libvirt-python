#!/usr/bin/env python3
# domstart - make sure a given domU is running, if not start it

import libvirt
import sys
import libxml2

# Parse the XML description of domU from FNAME
# and return a tuple (name, xmldesc) where NAME
# is the name of the domain, and xmldesc is the contetn of FNAME
def read_domain(fname):
    fp = open(fname, "r")
    xmldesc = fp.read()
    fp.close()

    doc = libxml2.parseDoc(xmldesc)
    name = doc.xpathNewContext().xpathEval("/domain/name")[0].content
    return (name, xmldesc)

def usage():
    print('Usage: %s domain.xml' % sys.argv[0])
    print('       Check that the domain described by DOMAIN.XML is running')
    print('       If the domain is not running, create it')
    print('       DOMAIN.XML must be a XML description of the domain')
    print('       in libvirt\'s XML format')

if len(sys.argv) != 2:
    usage()
    sys.exit(2)

(name, xmldesc) = read_domain(sys.argv[1])

try:
    conn = libvirt.open(None)
except libvirt.libvirtError:
    print('Failed to open connection to the hypervisor')
    sys.exit(1)

try:
    dom = conn.lookupByName(name)
except libvirt.libvirtError:
    print("Starting domain %s ... " % name)
    dom = conn.createLinux(xmldesc, 0)
    if dom is None:
        print("failed")
        sys.exit(1)
    else:
        print("done")
