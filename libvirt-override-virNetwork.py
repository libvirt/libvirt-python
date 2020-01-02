    def listAllPorts(self, flags=0):
        """List all ports on the network and returns a list of network port objects"""
        ret = libvirtmod.virNetworkListAllPorts(self._o, flags)
        if ret is None:
            raise libvirtError("virNetworkListAllPorts() failed", conn=self)

        retlist = list()
        for domptr in ret:
            retlist.append(virNetworkPort(self, _obj=domptr))

        return retlist
