    def getConnect(self) -> 'virConnect':
        """Get the connection that owns the domain that a checkpoint was created for"""
        return self.connect()

    def getDomain(self) -> 'virDomain':
        """Get the domain that a checkpoint was created for"""
        return self.domain()

    def listAllChildren(self, flags: int = 0) -> List['virDomainCheckpoint']:
        """List all child checkpoints and returns a list of checkpoint objects"""
        ret = libvirtmod.virDomainCheckpointListAllChildren(self._o, flags)
        if ret is None:
            raise libvirtError("virDomainCheckpointListAllChildren() failed")

        return [virDomainCheckpoint(self.domain(), _obj=chkptr) for chkptr in ret]
