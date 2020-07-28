#!/usr/bin/env python3
"""
Save all currently running domU's into DIR.
DIR must exist and be writable by this process.
"""

import libvirt
import sys
import os
import libxml2
import pdb
from argparse import ArgumentParser


parser = ArgumentParser(description=__doc__)
parser.add_argument("dir")
args = parser.parse_args()

try:
    conn = libvirt.open(None)
except libvirt.libvirtError:
    print('Failed to open connection to the hypervisor')
    sys.exit(1)

doms = conn.listDomainsID()
for id in doms:
    if id == 0:
        continue
    dom = conn.lookupByID(id)
    print("Saving %s[%d] ... " % (dom.name(), id))
    path = os.path.join(args.dir, dom.name())
    ret = dom.save(path)
    if ret == 0:
        print("done")
    else:
        print("error %d" % ret)

#pdb.set_trace()
