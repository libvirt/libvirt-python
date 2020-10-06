import unittest
import libvirt


class TestLibvirtNetwork(unittest.TestCase):
    def setUp(self):
        self.conn = libvirt.open("test:///default")
        self.net = self.conn.networkLookupByName("default")

    def tearDown(self):
        self.net = None
        self.conn = None

    def testAttr(self):
        self.assertEqual(self.net.name(), "default")
