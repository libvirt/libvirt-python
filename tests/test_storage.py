import unittest
import libvirt


class TestLibvirtStorage(unittest.TestCase):
    def setUp(self):
        self.conn = libvirt.open("test:///default")
        self.pool = self.conn.storagePoolLookupByName("default-pool")

    def tearDown(self):
        self.pool = None
        self.conn = None

    def testAttr(self):
        self.assertEqual(self.pool.name(), "default-pool")

    def testVol(self):
        volxml = '''<volume type="file">
  <name>raw.img</name>
  <allocation unit="M">10</allocation>
  <capacity unit="M">1000</capacity>
</volume>'''

        vol = self.pool.createXML(volxml)
