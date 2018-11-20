    def getConnect(self) -> 'virConnect':
        """Get the connection that owns the domain that a snapshot was created for"""
        return self.connect()

    def getDomain(self) -> 'virDomain':
        """Get the domain that a snapshot was created for"""
        return self.domain()

    def listAllChildren(self, flags: int = 0) -> List['virDomainSnapshot']:
        """List all child snapshots and returns a list of snapshot objects"""
        ret = libvirtmod.virDomainSnapshotListAllChildren(self._o, flags)
        if ret is None:
            raise libvirtError("virDomainSnapshotListAllChildren() failed")

        retlist = list()
        for snapptr in ret:
            retlist.append(virDomainSnapshot(self.domain(), _obj=snapptr))

        return retlist
