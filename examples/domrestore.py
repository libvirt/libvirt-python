#!/usr/bin/env python3
"""
Restore all the domains contained in DIR.
It is assumed that all files in DIR are images of domU's previously created with save.
"""

import libvirt
import os
from argparse import ArgumentParser


parser = ArgumentParser(description=__doc__)
parser.add_argument("dir")
args = parser.parse_args()

imgs = os.listdir(args.dir)

try:
    conn = libvirt.open(None)
except libvirt.libvirtError:
    print('Failed to open connection to the hypervisor')
    exit(1)

for img in imgs:
    file = os.path.join(args.dir, img)
    print("Restoring %s ... " % img)
    ret = conn.restore(file)
    if ret == 0:
        print("done")
    else:
        print("error %d" % ret)
