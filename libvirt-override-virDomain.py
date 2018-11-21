    def listAllSnapshots(self, flags: int = 0) -> List['virDomainSnapshot']:
        """List all snapshots and returns a list of snapshot objects"""
        ret = libvirtmod.virDomainListAllSnapshots(self._o, flags)
        if ret is None:
            raise libvirtError("virDomainListAllSnapshots() failed")

        return [virDomainSnapshot(self, _obj=snapptr) for snapptr in ret]

    def listAllCheckpoints(self, flags: int = 0) -> List['virDomainCheckpoint']:
        """List all checkpoints and returns a list of checkpoint objects"""
        ret = libvirtmod.virDomainListAllCheckpoints(self._o, flags)
        if ret is None:
            raise libvirtError("virDomainListAllCheckpoints() failed")

        return [virDomainCheckpoint(self, _obj=chkptr) for chkptr in ret]

    def createWithFiles(self, files: List[int], flags: int = 0) -> 'virDomain':
        """Launch a defined domain. If the call succeeds the domain moves from the
        defined to the running domains pools.

        @files provides an array of file descriptors which will be
        made available to the 'init' process of the guest. The file
        handles exposed to the guest will be renumbered to start
        from 3 (ie immediately following stderr). This is only
        supported for guests which use container based virtualization
        technology.

        If the VIR_DOMAIN_START_PAUSED flag is set, or if the guest domain
        has a managed save image that requested paused state (see
        virDomainManagedSave()) the guest domain will be started, but its
        CPUs will remain paused. The CPUs can later be manually started
        using virDomainResume().  In all other cases, the guest domain will
        be running.

        If the VIR_DOMAIN_START_AUTODESTROY flag is set, the guest
        domain will be automatically destroyed when the virConnectPtr
        object is finally released. This will also happen if the
        client application crashes / loses its connection to the
        libvirtd daemon. Any domains marked for auto destroy will
        block attempts at migration, save-to-file, or snapshots.

        If the VIR_DOMAIN_START_BYPASS_CACHE flag is set, and there is a
        managed save file for this domain (created by virDomainManagedSave()),
        then libvirt will attempt to bypass the file system cache while restoring
        the file, or fail if it cannot do so for the given system; this can allow
        less pressure on file system cache, but also risks slowing loads from NFS.

        If the VIR_DOMAIN_START_FORCE_BOOT flag is set, then any managed save
        file for this domain is discarded, and the domain boots from scratch. """
        ret = libvirtmod.virDomainCreateWithFiles(self._o, files, flags)
        if ret == -1:
            raise libvirtError('virDomainCreateWithFiles() failed')
        return ret

    def fsFreeze(self, mountpoints: List[str] = None, flags: int = 0) -> int:
        """Freeze specified filesystems within the guest """
        ret = libvirtmod.virDomainFSFreeze(self._o, mountpoints, flags)
        if ret == -1:
            raise libvirtError('virDomainFSFreeze() failed')
        return ret

    def fsThaw(self, mountpoints: List[str] = None, flags: int = 0) -> int:
        """Thaw specified filesystems within the guest """
        ret = libvirtmod.virDomainFSThaw(self._o, mountpoints, flags)
        if ret == -1:
            raise libvirtError('virDomainFSThaw() failed')
        return ret

    def getTime(self, flags: int = 0) -> int:
        """Extract information about guest time """
        ret = libvirtmod.virDomainGetTime(self._o, flags)
        if ret is None:
            raise libvirtError('virDomainGetTime() failed')
        return ret

    def setTime(self, time: int = None, flags: int = 0) -> int:
        """Set guest time to the given value. @time is a dict containing
        'seconds' field for seconds and 'nseconds' field for nanoseconds """
        ret = libvirtmod.virDomainSetTime(self._o, time, flags)
        if ret == -1:
            raise libvirtError('virDomainSetTime() failed')
        return ret
