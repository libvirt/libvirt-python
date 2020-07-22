#!/usr/bin/env python3
# domstart - make sure a given domU is running, if not start it

import libvirt
import sys
import os

def usage() -> None:
    print('Usage: %s DIR' % sys.argv[0])
    print('       Restore all the domains contained in DIR')
    print('       It is assumed that all files in DIR are')
    print('       images of domU\'s previously created with save')

if len(sys.argv) != 2:
    usage()
    sys.exit(2)

dir = sys.argv[1]
imgs = os.listdir(dir)

try:
    conn = libvirt.open(None)
except libvirt.libvirtError:
    print('Failed to open connection to the hypervisor')
    sys.exit(1)

for img in imgs:
    file = os.path.join(dir, img)
    print("Restoring %s ... " % img)
    ret = conn.restore(file)
    if ret == 0:
        print("done")
    else:
        print("error %d" % ret)
