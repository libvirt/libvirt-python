import unittest
import libvirt


class TestLibvirtInterface(unittest.TestCase):
    def setUp(self):
        self.conn = libvirt.open("test:///default")
        self.iface = self.conn.interfaceLookupByName("eth1")

    def tearDown(self):
        self.iface = None
        self.conn = None

    def testAttr(self):
        self.assertEqual(self.iface.name(), "eth1")
