import unittest
import libvirt


class TestLibvirtDomainSnapshot(unittest.TestCase):
    def setUp(self):
        self.conn = libvirt.open("test:///default")
        self.dom = self.conn.lookupByName("test")

    def tearDown(self):
        self.dom = None
        self.conn = None

    def testSnapCreate(self):
        snap = self.dom.snapshotCreateXML("<domainsnapshot/>")
        snap.delete()
