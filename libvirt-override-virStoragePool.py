    def listAllVolumes(self, flags: int = 0) -> List['virStorageVol']:
        """List all storage volumes and returns a list of storage volume objects"""
        ret = libvirtmod.virStoragePoolListAllVolumes(self._o, flags)
        if ret is None:
            raise libvirtError("virStoragePoolListAllVolumes() failed")

        return [virStorageVol(self._conn, _obj=volptr) for volptr in ret]
