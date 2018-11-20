#!/usr/bin/env python3
"""
Either uploads local FILE to libvirt VOLUME, or downloads libvirt
VOLUME into local FILE while preserving FILE/VOLUME sparseness
"""
# Example of sparse streams usage
#
# Authors:
#   Michal Privoznik <mprivozn@redhat.com>

import libvirt
import os
from argparse import ArgumentParser


def bytesWriteHandler(stream: libvirt.virStream, buf: bytes, opaque: int) -> int:
    fd = opaque
    return os.write(fd, buf)


def bytesReadHandler(stream: libvirt.virStream, nbytes: int, opaque: int) -> bytes:
    fd = opaque
    return os.read(fd, nbytes)


def recvSkipHandler(stream: libvirt.virStream, length: int, opaque: int) -> None:
    fd = opaque
    cur = os.lseek(fd, length, os.SEEK_CUR)
    return os.ftruncate(fd, cur)


def sendSkipHandler(stream: libvirt.virStream, length: int, opaque: int) -> int:
    fd = opaque
    return os.lseek(fd, length, os.SEEK_CUR)


def holeHandler(stream: libvirt.virStream, opaque: int):
    fd = opaque
    cur = os.lseek(fd, 0, os.SEEK_CUR)

    try:
        data = os.lseek(fd, cur, os.SEEK_DATA)
    except OSError as e:
        if e.errno != 6:
            raise e
        else:
            data = -1
    # There are three options:
    # 1) data == cur;  @cur is in data
    # 2) data > cur; @cur is in a hole, next data at @data
    # 3) data < 0; either @cur is in trailing hole, or @cur is beyond EOF.
    if data < 0:
        # case 3
        inData = False
        eof = os.lseek(fd, 0, os.SEEK_END)
        if (eof < cur):
            raise RuntimeError("Current position in file after EOF: %d" % cur)
        sectionLen = eof - cur
    else:
        if (data > cur):
            # case 2
            inData = False
            sectionLen = data - cur
        else:
            # case 1
            inData = True

            # We don't know where does the next hole start. Let's find out.
            # Here we get the same options as above
            hole = os.lseek(fd, data, os.SEEK_HOLE)
            if hole < 0:
                # case 3. But wait a second. There is always a trailing hole.
                # Do the best what we can here
                raise RuntimeError("No trailing hole")

            if (hole == data):
                # case 1. Again, this is suspicious. The reason we are here is
                # because we are in data. But at the same time we are in a
                # hole. WAT?
                raise RuntimeError("Impossible happened")
            else:
                # case 2
                sectionLen = hole - data
    os.lseek(fd, cur, os.SEEK_SET)
    return [inData, sectionLen]


def download(vol: libvirt.virStorageVol, st: libvirt.virStream, filename: str) -> None:
    offset = 0
    length = 0

    fd = os.open(filename, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, mode=0o0660)
    vol.download(st, offset, length, libvirt.VIR_STORAGE_VOL_DOWNLOAD_SPARSE_STREAM)
    st.sparseRecvAll(bytesWriteHandler, recvSkipHandler, fd)

    os.close(fd)


def upload(vol: libvirt.virStorageVol, st: libvirt.virStream, filename: str) -> None:
    offset = 0
    length = 0

    fd = os.open(filename, os.O_RDONLY)
    vol.upload(st, offset, length, libvirt.VIR_STORAGE_VOL_UPLOAD_SPARSE_STREAM)
    st.sparseSendAll(bytesReadHandler, holeHandler, sendSkipHandler, fd)

    os.close(fd)


# main
parser = ArgumentParser(description=__doc__)
parser.add_argument("uri")
group = parser.add_mutually_exclusive_group(required=True)
group.add_argument("--upload", action="store_const", const=upload, dest="operation")
group.add_argument("--download", action="store_const", const=download, dest="operation")
parser.add_argument("volume")
parser.add_argument("file")
args = parser.parse_args()


conn = libvirt.open(args.uri)
vol = conn.storageVolLookupByKey(args.volume)

st = conn.newStream()

args.operation(vol, st, args.file)

st.finish()
conn.close()
