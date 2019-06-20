    def listAllPorts(self, flags=0):
        """List all domains and returns a list of domain objects"""
        ret = libvirtmod.virNetworkListAllPorts(self._o, flags)
        if ret is None:
            raise libvirtError("virNetworkListAllPorts() failed", conn=self)

        retlist = list()
        for domptr in ret:
            retlist.append(virNetwork(self, _obj=domptr))

        return retlist
