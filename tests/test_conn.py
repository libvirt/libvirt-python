import unittest
import libvirt
import tempfile
import contextlib
import os


class TestLibvirtConn(unittest.TestCase):
    def setUp(self):
        self.conn = libvirt.open("test:///default")

    def tearDown(self):
        self.conn = None

    def testConnDomainList(self):
        doms = self.conn.listAllDomains()
        self.assertEqual(len(doms), 1)
        self.assertEqual(type(doms[0]), libvirt.virDomain)
        self.assertEqual(doms[0].name(), "test")

class TestLibvirtConnAuth(unittest.TestCase):
    connXML = """
<node>
  <auth>
    <user password="2147483647">marin</user>
    <user password="87539319">srinivasa</user>
  </auth>
</node>"""
    def setUp(self):
        def noop(msg, opaque):
            pass
        libvirt.registerErrorHandler(noop, None)

    @contextlib.contextmanager
    def tempxmlfile(content):
        try:
            fp = tempfile.NamedTemporaryFile(delete=False,
                                             prefix="libvirt-python-test",
                                             suffix=".xml")
            fname = fp.name
            fp.write(content.encode("utf8"))
            fp.close()
            yield fname
        finally:
            os.unlink(fname)

    def authHelper(self, username, password):
        with TestLibvirtConnAuth.tempxmlfile(self.connXML) as fname:
            magic = 142857
            def authCB(creds, opaque):
                if opaque != magic:
                    return -1

                for cred in creds:
                    if (cred[0] == libvirt.VIR_CRED_AUTHNAME and
                        username is not None):
                        cred[4] = username
                        return 0
                    elif (cred[0] == libvirt.VIR_CRED_PASSPHRASE and
                          password is not None):
                        cred[4] = password
                        return 0
                    return -1
                return 0

            auth = [[libvirt.VIR_CRED_AUTHNAME,
                     libvirt.VIR_CRED_ECHOPROMPT,
                     libvirt.VIR_CRED_REALM,
                     libvirt.VIR_CRED_PASSPHRASE,
                     libvirt.VIR_CRED_NOECHOPROMPT,
                     libvirt.VIR_CRED_EXTERNAL],
                    authCB, magic]

            return libvirt.openAuth("test://" + fname,
                                    auth, 0)

    def testOpenAuthGood(self):
        conn = self.authHelper("srinivasa", "87539319")

    def testOpenAuthBad(self):
        try:
            conn = self.authHelper("srinivasa", "2147483647")
            raise Exception("Unexpected open success")
        except libvirt.libvirtError as ex:
            pass

    def testOpenAuthNone(self):
        try:
            conn = self.authHelper(None, None)
            raise Exception("Unexpected open success")
        except libvirt.libvirtError as ex:
            pass
