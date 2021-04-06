import unittest
import libvirt


class TestLibvirtDomain(unittest.TestCase):
    def setUp(self):
        self.conn = libvirt.open("test:///default")
        self.dom = self.conn.lookupByName("test")

    def tearDown(self):
        self.dom = None
        self.conn = None

    def testDomainSchedParams(self):
        params = self.dom.schedulerParameters()
        self.assertEqual(len(params), 1)
        self.assertTrue("weight" in params)
        params["weight"] = 100
        self.dom.setSchedulerParameters(params)

    @unittest.skipIf(libvirt.getVersion() == 4000000,
                     "test driver screenshot broken in 4.0.0")
    def testScreenshot(self):
        stream = self.conn.newStream()
        ss = self.dom.screenshot(stream, 0, 0)
