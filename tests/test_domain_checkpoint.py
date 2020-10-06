import unittest
import libvirt


class TestLibvirtDomainCheckpoint(unittest.TestCase):
    def setUp(self):
        self.conn = libvirt.open("test:///default")
        self.dom = self.conn.lookupByName("test")

    def tearDown(self):
        self.dom = None
        self.conn = None

    @unittest.skipUnless(hasattr(libvirt.virDomain, "checkpointCreateXML"),
                         "checkpoints not supported in this libvirt")
    def testCheckpointCreate(self):
        cp = self.dom.checkpointCreateXML("<domaincheckpoint/>")
        cp.delete()
