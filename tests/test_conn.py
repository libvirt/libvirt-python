
import unittest
import libvirt

class TestLibvirtConn(unittest.TestCase):
    def setUp(self):
        self.conn = libvirt.open("test:///default")

    def tearDown(self):
        self.conn = None

    def testConnDomainList(self):
        doms = self.conn.listAllDomains()
        self.assertEquals(len(doms), 1)
        self.assertEquals(type(doms[0]), libvirt.virDomain)
        self.assertEquals(doms[0].name(), "test")
