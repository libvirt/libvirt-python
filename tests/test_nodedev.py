import unittest
import libvirt


class TestLibvirtNodeDev(unittest.TestCase):
    def setUp(self):
        self.conn = libvirt.open("test:///default")
        self.nodedev = self.conn.nodeDeviceLookupByName("computer")

    def tearDown(self):
        self.nodedev = None
        self.conn = None

    def testAttr(self):
        self.assertEqual(self.nodedev.name(), "computer")
