#!/usr/bin/env python3
"""
Check that the domain described by DOMAIN.XML is running.
If the domain is not running, create it.
"""

import libvirt
import libxml2
from argparse import ArgumentParser
from typing import Tuple


# Parse the XML description of domU from FNAME
# and return a tuple (name, xmldesc) where NAME
# is the name of the domain, and xmldesc is the contetn of FNAME
def read_domain(fname: str) -> Tuple[str, str]:
    fp = open(fname, "r")
    xmldesc = fp.read()
    fp.close()

    doc = libxml2.parseDoc(xmldesc)
    name = doc.xpathNewContext().xpathEval("/domain/name")[0].content
    return (name, xmldesc)


parser = ArgumentParser(description=__doc__)
parser.add_argument("file", metavar="DOMAIN.XML", help="XML configuration of the domain in libvirt's XML format")
args = parser.parse_args()

(name, xmldesc) = read_domain(args.file)

try:
    conn = libvirt.open(None)
except libvirt.libvirtError:
    print('Failed to open connection to the hypervisor')
    exit(1)

try:
    dom = conn.lookupByName(name)
except libvirt.libvirtError:
    print("Starting domain %s ... " % name)
    dom = conn.createLinux(xmldesc, 0)
    if dom is None:
        print("failed")
        exit(1)
    else:
        print("done")
