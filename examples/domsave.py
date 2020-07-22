#!/usr/bin/env python3
# domstart - make sure a given domU is running, if not start it

import libvirt
import sys
import os

def usage():
   print('Usage: %s DIR' % sys.argv[0])
   print('       Save all currently running domU\'s into DIR')
   print('       DIR must exist and be writable by this process')

if len(sys.argv) != 2:
    usage()
    sys.exit(2)

dir = sys.argv[1]

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
    path = os.path.join(dir, dom.name())
    ret = dom.save(path)
    if ret == 0:
        print("done")
    else:
        print("error %d" % ret)

# import pdb; pdb.set_trace()
