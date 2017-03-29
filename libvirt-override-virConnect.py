    def __del__(self):
        try:
           for cb,opaque in self.domainEventCallbacks.items():
               del self.domainEventCallbacks[cb]
           del self.domainEventCallbacks
           libvirtmod.virConnectDomainEventDeregister(self._o, self)
        except AttributeError:
           pass

        if self._o is not None:
            libvirtmod.virConnectClose(self._o)
        self._o = None

    def domainEventDeregister(self, cb):
        """Removes a Domain Event Callback. De-registering for a
           domain callback will disable delivery of this event type """
        try:
            del self.domainEventCallbacks[cb]
            if len(self.domainEventCallbacks) == 0:
                del self.domainEventCallbacks
                ret = libvirtmod.virConnectDomainEventDeregister(self._o, self)
                if ret == -1: raise libvirtError ('virConnectDomainEventDeregister() failed', conn=self)
        except AttributeError:
            pass

    def domainEventRegister(self, cb, opaque):
        """Adds a Domain Event Callback. Registering for a domain
           callback will enable delivery of the events """
        try:
            self.domainEventCallbacks[cb] = opaque
        except AttributeError:
            self.domainEventCallbacks = {cb:opaque}
            ret = libvirtmod.virConnectDomainEventRegister(self._o, self)
            if ret == -1: raise libvirtError ('virConnectDomainEventRegister() failed', conn=self)

    def _dispatchDomainEventCallbacks(self, dom, event, detail):
        """Dispatches events to python user domain event callbacks
        """
        try:
            for cb,opaque in self.domainEventCallbacks.items():
                cb(self, virDomain(self, _obj=dom), event, detail, opaque)
            return 0
        except AttributeError:
            pass

    def _dispatchDomainEventLifecycleCallback(self, dom, event, detail, cbData):
        """Dispatches events to python user domain lifecycle event callbacks
        """
        cb = cbData["cb"]
        opaque = cbData["opaque"]

        cb(self, virDomain(self, _obj=dom), event, detail, opaque)
        return 0

    def _dispatchDomainEventGenericCallback(self, dom, cbData):
        """Dispatches events to python user domain generic event callbacks
        """
        cb = cbData["cb"]
        opaque = cbData["opaque"]

        cb(self, virDomain(self, _obj=dom), opaque)
        return 0

    def _dispatchDomainEventRTCChangeCallback(self, dom, offset, cbData):
        """Dispatches events to python user domain RTC change event callbacks
        """
        cb = cbData["cb"]
        opaque = cbData["opaque"]

        cb(self, virDomain(self, _obj=dom), offset ,opaque)
        return 0

    def _dispatchDomainEventWatchdogCallback(self, dom, action, cbData):
        """Dispatches events to python user domain watchdog event callbacks
        """
        cb = cbData["cb"]
        opaque = cbData["opaque"]

        cb(self, virDomain(self, _obj=dom), action, opaque)
        return 0

    def _dispatchDomainEventIOErrorCallback(self, dom, srcPath, devAlias,
                                            action, cbData):
        """Dispatches events to python user domain IO error event callbacks
        """
        cb = cbData["cb"]
        opaque = cbData["opaque"]

        cb(self, virDomain(self, _obj=dom), srcPath, devAlias, action, opaque)
        return 0

    def _dispatchDomainEventIOErrorReasonCallback(self, dom, srcPath,
                                                  devAlias, action, reason,
                                                  cbData):
        """Dispatches events to python user domain IO error event callbacks
        """
        cb = cbData["cb"]
        opaque = cbData["opaque"]

        cb(self, virDomain(self, _obj=dom), srcPath, devAlias, action,
           reason, opaque)
        return 0

    def _dispatchDomainEventGraphicsCallback(self, dom, phase, localAddr,
                                            remoteAddr, authScheme, subject,
                                            cbData):
        """Dispatches events to python user domain graphics event callbacks
        """
        cb = cbData["cb"]
        opaque = cbData["opaque"]

        cb(self, virDomain(self, _obj=dom), phase, localAddr, remoteAddr,
           authScheme, subject, opaque)
        return 0

    def _dispatchDomainEventBlockJobCallback(self, dom, disk, type, status, cbData):
        """Dispatches events to python user domain blockJob/blockJob2 event callbacks
        """
        try:
            cb = cbData["cb"]
            opaque = cbData["opaque"]

            cb(self, virDomain(self, _obj=dom), disk, type, status, opaque)
            return 0
        except AttributeError:
            pass

    def _dispatchDomainEventDiskChangeCallback(self, dom, oldSrcPath, newSrcPath, devAlias, reason, cbData):
        """Dispatches event to python user domain diskChange event callbacks
        """
        cb = cbData["cb"]
        opaque = cbData["opaque"]

        cb(self, virDomain(self, _obj=dom), oldSrcPath, newSrcPath, devAlias, reason, opaque)
        return 0

    def _dispatchDomainEventTrayChangeCallback(self, dom, devAlias, reason, cbData):
        """Dispatches event to python user domain trayChange event callbacks
        """
        cb = cbData["cb"]
        opaque = cbData["opaque"]

        cb(self, virDomain(self, _obj=dom), devAlias, reason, opaque)
        return 0

    def _dispatchDomainEventPMWakeupCallback(self, dom, reason, cbData):
        """Dispatches event to python user domain pmwakeup event callbacks
        """
        cb = cbData["cb"]
        opaque = cbData["opaque"]

        cb(self, virDomain(self, _obj=dom), reason, opaque)
        return 0

    def _dispatchDomainEventPMSuspendCallback(self, dom, reason, cbData):
        """Dispatches event to python user domain pmsuspend event callbacks
        """
        cb = cbData["cb"]
        opaque = cbData["opaque"]

        cb(self, virDomain(self, _obj=dom), reason, opaque)
        return 0

    def _dispatchDomainEventBalloonChangeCallback(self, dom, actual, cbData):
        """Dispatches events to python user domain balloon change event callbacks
        """
        cb = cbData["cb"]
        opaque = cbData["opaque"]

        cb(self, virDomain(self, _obj=dom), actual, opaque)
        return 0

    def _dispatchDomainEventPMSuspendDiskCallback(self, dom, reason, cbData):
        """Dispatches event to python user domain pmsuspend-disk event callbacks
        """
        cb = cbData["cb"]
        opaque = cbData["opaque"]

        cb(self, virDomain(self, _obj=dom), reason, opaque)
        return 0

    def _dispatchDomainEventDeviceRemovedCallback(self, dom, devAlias, cbData):
        """Dispatches event to python user domain device removed event callbacks
        """
        cb = cbData["cb"]
        opaque = cbData["opaque"]

        cb(self, virDomain(self, _obj=dom), devAlias, opaque)
        return 0

    def _dispatchDomainEventTunableCallback(self, dom, params, cbData):
        """Dispatches event to python user domain tunable event callbacks
        """
        cb = cbData["cb"]
        opaque = cbData["opaque"]

        cb(self, virDomain(self, _obj=dom), params, opaque)
        return 0

    def _dispatchDomainEventAgentLifecycleCallback(self, dom, state, reason, cbData):
        """Dispatches event to python user domain agent lifecycle event callback
        """

        cb = cbData["cb"]
        opaque = cbData["opaque"]

        cb(self, virDomain(self, _obj=dom), state, reason, opaque)
        return 0

    def _dispatchDomainEventDeviceAddedCallback(self, dom, devAlias, cbData):
        """Dispatches event to python user domain device added event callbacks
        """
        cb = cbData["cb"]
        opaque = cbData["opaque"]

        cb(self, virDomain(self, _obj=dom), devAlias, opaque)
        return 0

    def _dispatchDomainEventMigrationIterationCallback(self, dom, iteration, cbData):
        """Dispatches event to python user domain migration iteration event callbacks
        """
        cb = cbData["cb"]
        opaque = cbData["opaque"]

        cb(self, virDomain(self, _obj=dom), iteration, opaque)
        return 0

    def _dispatchDomainEventJobCompletedCallback(self, dom, params, cbData):
        """Dispatches event to python user domain job completed callbacks
        """
        cb = cbData["cb"]
        opaque = cbData["opaque"]

        cb(self, virDomain(self, _obj=dom), params, opaque)
        return 0

    def _dispatchDomainEventDeviceRemovalFailedCallback(self, dom, devAlias, cbData):
        """Dispatches event to python user domain device removal failed event callbacks
        """
        cb = cbData["cb"]
        opaque = cbData["opaque"]

        cb(self, virDomain(self, _obj=dom), devAlias, opaque)
        return 0

    def _dispatchDomainEventMetadataChangeCallback(self, dom, mtype, nsuri, cbData):
        """Dispatches event to python user domain metadata change event callbacks
        """
        cb = cbData["cb"]
        opaque = cbData["opaque"]

        cb(self, virDomain(self, _obj=dom), mtype, nsuri, opaque)
        return 0

    def _dispatchDomainEventBlockThresholdCallback(self, dom, dev, path, threshold, excess, cbData):
        """Dispatches event to python user domain block device threshold event callbacks
        """
        cb = cbData["cb"]
        opaque = cbData["opaque"]

        cb(self, virDomain(self, _obj=dom), dev, path, threshold, excess, opaque)
        return 0

    def domainEventDeregisterAny(self, callbackID):
        """Removes a Domain Event Callback. De-registering for a
           domain callback will disable delivery of this event type """
        try:
            ret = libvirtmod.virConnectDomainEventDeregisterAny(self._o, callbackID)
            if ret == -1: raise libvirtError ('virConnectDomainEventDeregisterAny() failed', conn=self)
            del self.domainEventCallbackID[callbackID]
        except AttributeError:
            pass

    def _dispatchNetworkEventLifecycleCallback(self, net, event, detail, cbData):
        """Dispatches events to python user network lifecycle event callbacks
        """
        cb = cbData["cb"]
        opaque = cbData["opaque"]

        cb(self, virNetwork(self, _obj=net), event, detail, opaque)
        return 0

    def networkEventDeregisterAny(self, callbackID):
        """Removes a Network Event Callback. De-registering for a
           network callback will disable delivery of this event type"""
        try:
            ret = libvirtmod.virConnectNetworkEventDeregisterAny(self._o, callbackID)
            if ret == -1: raise libvirtError ('virConnectNetworkEventDeregisterAny() failed', conn=self)
            del self.networkEventCallbackID[callbackID]
        except AttributeError:
            pass

    def networkEventRegisterAny(self, net, eventID, cb, opaque):
        """Adds a Network Event Callback. Registering for a network
           callback will enable delivery of the events"""
        if not hasattr(self, 'networkEventCallbackID'):
            self.networkEventCallbackID = {}
        cbData = { "cb": cb, "conn": self, "opaque": opaque }
        if net is None:
            ret = libvirtmod.virConnectNetworkEventRegisterAny(self._o, None, eventID, cbData)
        else:
            ret = libvirtmod.virConnectNetworkEventRegisterAny(self._o, net._o, eventID, cbData)
        if ret == -1:
            raise libvirtError ('virConnectNetworkEventRegisterAny() failed', conn=self)
        self.networkEventCallbackID[ret] = opaque
        return ret

    def domainEventRegisterAny(self, dom, eventID, cb, opaque):
        """Adds a Domain Event Callback. Registering for a domain
           callback will enable delivery of the events """
        if not hasattr(self, 'domainEventCallbackID'):
            self.domainEventCallbackID = {}
        cbData = { "cb": cb, "conn": self, "opaque": opaque }
        if dom is None:
            ret = libvirtmod.virConnectDomainEventRegisterAny(self._o, None, eventID, cbData)
        else:
            ret = libvirtmod.virConnectDomainEventRegisterAny(self._o, dom._o, eventID, cbData)
        if ret == -1:
            raise libvirtError ('virConnectDomainEventRegisterAny() failed', conn=self)
        self.domainEventCallbackID[ret] = opaque
        return ret

    def _dispatchStoragePoolEventLifecycleCallback(self, pool, event, detail, cbData):
        """Dispatches events to python user storage pool
           lifecycle event callbacks
        """
        cb = cbData["cb"]
        opaque = cbData["opaque"]

        cb(self, virStoragePool(self, _obj=pool), event, detail, opaque)
        return 0

    def _dispatchStoragePoolEventGenericCallback(self, pool, cbData):
        """Dispatches events to python user storage pool
           generic event callbacks
        """
        cb = cbData["cb"]
        opaque = cbData["opaque"]

        cb(self, virStoragePool(self, _obj=pool), opaque)
        return 0

    def storagePoolEventDeregisterAny(self, callbackID):
        """Removes a Storage Pool Event Callback. De-registering for a
           storage pool callback will disable delivery of this event type"""
        try:
            ret = libvirtmod.virConnectStoragePoolEventDeregisterAny(self._o, callbackID)
            if ret == -1: raise libvirtError ('virConnectStoragePoolEventDeregisterAny() failed', conn=self)
            del self.storagePoolEventCallbackID[callbackID]
        except AttributeError:
            pass

    def storagePoolEventRegisterAny(self, pool, eventID, cb, opaque):
        """Adds a Storage Pool Event Callback. Registering for a storage pool
           callback will enable delivery of the events"""
        if not hasattr(self, 'storagePoolEventCallbackID'):
            self.storagePoolEventCallbackID = {}
        cbData = { "cb": cb, "conn": self, "opaque": opaque }
        if pool is None:
            ret = libvirtmod.virConnectStoragePoolEventRegisterAny(self._o, None, eventID, cbData)
        else:
            ret = libvirtmod.virConnectStoragePoolEventRegisterAny(self._o, pool._o, eventID, cbData)
        if ret == -1:
            raise libvirtError ('virConnectStoragePoolEventRegisterAny() failed', conn=self)
        self.storagePoolEventCallbackID[ret] = opaque
        return ret

    def _dispatchNodeDeviceEventLifecycleCallback(self, dev, event, detail, cbData):
        """Dispatches events to python user node device
           lifecycle event callbacks
        """
        cb = cbData["cb"]
        opaque = cbData["opaque"]

        cb(self, virNodeDevice(self, _obj=dev), event, detail, opaque)
        return 0

    def _dispatchNodeDeviceEventGenericCallback(self, dev, cbData):
        """Dispatches events to python user node device
           generic event callbacks
        """
        cb = cbData["cb"]
        opaque = cbData["opaque"]

        cb(self, virNodeDevice(self, _obj=dev), opaque)
        return 0

    def nodeDeviceEventDeregisterAny(self, callbackID):
        """Removes a Node Device Event Callback. De-registering for a
           node device callback will disable delivery of this event type"""
        try:
            ret = libvirtmod.virConnectNodeDeviceEventDeregisterAny(self._o, callbackID)
            if ret == -1: raise libvirtError ('virConnectNodeDeviceEventDeregisterAny() failed', conn=self)
            del self.nodeDeviceEventCallbackID[callbackID]
        except AttributeError:
            pass

    def nodeDeviceEventRegisterAny(self, dev, eventID, cb, opaque):
        """Adds a Node Device Event Callback. Registering for a node device
           callback will enable delivery of the events"""
        if not hasattr(self, 'nodeDeviceEventCallbackID'):
            self.nodeDeviceEventCallbackID = {}
        cbData = { "cb": cb, "conn": self, "opaque": opaque }
        if dev is None:
            ret = libvirtmod.virConnectNodeDeviceEventRegisterAny(self._o, None, eventID, cbData)
        else:
            ret = libvirtmod.virConnectNodeDeviceEventRegisterAny(self._o, dev._o, eventID, cbData)
        if ret == -1:
            raise libvirtError ('virConnectNodeDeviceEventRegisterAny() failed', conn=self)
        self.nodeDeviceEventCallbackID[ret] = opaque
        return ret

    def _dispatchSecretEventLifecycleCallback(self, secret, event, detail, cbData):
        """Dispatches events to python user secret lifecycle event callbacks
        """
        cb = cbData["cb"]
        opaque = cbData["opaque"]

        cb(self, virSecret(self, _obj=secret), event, detail, opaque)
        return 0

    def _dispatchSecretEventGenericCallback(self, secret, cbData):
        """Dispatches events to python user secret generic event callbacks
        """
        cb = cbData["cb"]
        opaque = cbData["opaque"]

        cb(self, virSecret(self, _obj=secret), opaque)
        return 0

    def secretEventDeregisterAny(self, callbackID):
        """Removes a Secret Event Callback. De-registering for a
           secret callback will disable delivery of this event type"""
        try:
            ret = libvirtmod.virConnectSecretEventDeregisterAny(self._o, callbackID)
            if ret == -1: raise libvirtError ('virConnectSecretEventDeregisterAny() failed', conn=self)
            del self.secretEventCallbackID[callbackID]
        except AttributeError:
            pass

    def secretEventRegisterAny(self, secret, eventID, cb, opaque):
        """Adds a Secret Event Callback. Registering for a secret
           callback will enable delivery of the events"""
        if not hasattr(self, 'secretEventCallbackID'):
            self.secretEventCallbackID = {}
        cbData = { "cb": cb, "conn": self, "opaque": opaque }
        if secret is None:
            ret = libvirtmod.virConnectSecretEventRegisterAny(self._o, None, eventID, cbData)
        else:
            ret = libvirtmod.virConnectSecretEventRegisterAny(self._o, secret._o, eventID, cbData)
        if ret == -1:
            raise libvirtError ('virConnectSecretEventRegisterAny() failed', conn=self)
        self.secretEventCallbackID[ret] = opaque
        return ret

    def listAllDomains(self, flags=0):
        """List all domains and returns a list of domain objects"""
        ret = libvirtmod.virConnectListAllDomains(self._o, flags)
        if ret is None:
            raise libvirtError("virConnectListAllDomains() failed", conn=self)

        retlist = list()
        for domptr in ret:
            retlist.append(virDomain(self, _obj=domptr))

        return retlist

    def listAllStoragePools(self, flags=0):
        """Returns a list of storage pool objects"""
        ret = libvirtmod.virConnectListAllStoragePools(self._o, flags)
        if ret is None:
            raise libvirtError("virConnectListAllStoragePools() failed", conn=self)

        retlist = list()
        for poolptr in ret:
            retlist.append(virStoragePool(self, _obj=poolptr))

        return retlist

    def listAllNetworks(self, flags=0):
        """Returns a list of network objects"""
        ret = libvirtmod.virConnectListAllNetworks(self._o, flags)
        if ret is None:
            raise libvirtError("virConnectListAllNetworks() failed", conn=self)

        retlist = list()
        for netptr in ret:
            retlist.append(virNetwork(self, _obj=netptr))

        return retlist

    def listAllInterfaces(self, flags=0):
        """Returns a list of interface objects"""
        ret = libvirtmod.virConnectListAllInterfaces(self._o, flags)
        if ret is None:
            raise libvirtError("virConnectListAllInterfaces() failed", conn=self)

        retlist = list()
        for ifaceptr in ret:
            retlist.append(virInterface(self, _obj=ifaceptr))

        return retlist

    def listAllDevices(self, flags=0):
        """Returns a list of host node device objects"""
        ret = libvirtmod.virConnectListAllNodeDevices(self._o, flags)
        if ret is None:
            raise libvirtError("virConnectListAllNodeDevices() failed", conn=self)

        retlist = list()
        for devptr in ret:
            retlist.append(virNodeDevice(self, _obj=devptr))

        return retlist

    def listAllNWFilters(self, flags=0):
        """Returns a list of network filter objects"""
        ret = libvirtmod.virConnectListAllNWFilters(self._o, flags)
        if ret is None:
            raise libvirtError("virConnectListAllNWFilters() failed", conn=self)

        retlist = list()
        for filter_ptr in ret:
            retlist.append(virNWFilter(self, _obj=filter_ptr))

        return retlist

    def listAllSecrets(self, flags=0):
        """Returns a list of secret objects"""
        ret = libvirtmod.virConnectListAllSecrets(self._o, flags)
        if ret is None:
            raise libvirtError("virConnectListAllSecrets() failed", conn=self)

        retlist = list()
        for secret_ptr in ret:
            retlist.append(virSecret(self, _obj=secret_ptr))

        return retlist

    def _dispatchCloseCallback(self, reason, cbData):
        """Dispatches events to python user close callback"""
        cb = cbData["cb"]
        opaque = cbData["opaque"]

        cb(self, reason, opaque)
        return 0


    def unregisterCloseCallback(self):
        """Removes a close event callback"""
        ret = libvirtmod.virConnectUnregisterCloseCallback(self._o)
        if ret == -1: raise libvirtError ('virConnectUnregisterCloseCallback() failed', conn=self)

    def registerCloseCallback(self, cb, opaque):
        """Adds a close event callback, providing a notification
         when a connection fails / closes"""
        cbData = { "cb": cb, "conn": self, "opaque": opaque }
        ret = libvirtmod.virConnectRegisterCloseCallback(self._o, cbData)
        if ret == -1:
            raise libvirtError ('virConnectRegisterCloseCallback() failed', conn=self)
        return ret

    def createXMLWithFiles(self, xmlDesc, files, flags=0):
        """Launch a new guest domain, based on an XML description similar
        to the one returned by virDomainGetXMLDesc()
        This function may require privileged access to the hypervisor.
        The domain is not persistent, so its definition will disappear when it
        is destroyed, or if the host is restarted (see virDomainDefineXML() to
        define persistent domains).

        @files provides an array of file descriptors which will be
        made available to the 'init' process of the guest. The file
        handles exposed to the guest will be renumbered to start
        from 3 (ie immediately following stderr). This is only
        supported for guests which use container based virtualization
        technology.

        If the VIR_DOMAIN_START_PAUSED flag is set, the guest domain
        will be started, but its CPUs will remain paused. The CPUs
        can later be manually started using virDomainResume.

        If the VIR_DOMAIN_START_AUTODESTROY flag is set, the guest
        domain will be automatically destroyed when the virConnectPtr
        object is finally released. This will also happen if the
        client application crashes / loses its connection to the
        libvirtd daemon. Any domains marked for auto destroy will
        block attempts at migration, save-to-file, or snapshots. """
        ret = libvirtmod.virDomainCreateXMLWithFiles(self._o, xmlDesc, files, flags)
        if ret is None:raise libvirtError('virDomainCreateXMLWithFiles() failed', conn=self)
        __tmp = virDomain(self,_obj=ret)
        return __tmp

    def getAllDomainStats(self, stats = 0, flags=0):
        """Query statistics for all domains on a given connection.

        Report statistics of various parameters for a running VM according to @stats
        field. The statistics are returned as an array of structures for each queried
        domain. The structure contains an array of typed parameters containing the
        individual statistics. The typed parameter name for each statistic field
        consists of a dot-separated string containing name of the requested group
        followed by a group specific description of the statistic value.

        The statistic groups are enabled using the @stats parameter which is a
        binary-OR of enum virDomainStatsTypes. The following groups are available
        (although not necessarily implemented for each hypervisor):

        VIR_DOMAIN_STATS_STATE: Return domain state and reason for entering that
        state. The typed parameter keys are in this format:
        "state.state" - state of the VM, returned as int from virDomainState enum
        "state.reason" - reason for entering given state, returned as int from
                         virDomain*Reason enum corresponding to given state.

        Using 0 for @stats returns all stats groups supported by the given
        hypervisor.

        Specifying VIR_CONNECT_GET_ALL_DOMAINS_STATS_ENFORCE_STATS as @flags makes
        the function return error in case some of the stat types in @stats were
        not recognized by the daemon.

        Similarly to virConnectListAllDomains, @flags can contain various flags to
        filter the list of domains to provide stats for.

        VIR_CONNECT_GET_ALL_DOMAINS_STATS_ACTIVE selects online domains while
        VIR_CONNECT_GET_ALL_DOMAINS_STATS_INACTIVE selects offline ones.

        VIR_CONNECT_GET_ALL_DOMAINS_STATS_PERSISTENT and
        VIR_CONNECT_GET_ALL_DOMAINS_STATS_TRANSIENT allow to filter the list
        according to their persistence.

        To filter the list of VMs by domain state @flags can contain
        VIR_CONNECT_GET_ALL_DOMAINS_STATS_RUNNING,
        VIR_CONNECT_GET_ALL_DOMAINS_STATS_PAUSED,
        VIR_CONNECT_GET_ALL_DOMAINS_STATS_SHUTOFF and/or
        VIR_CONNECT_GET_ALL_DOMAINS_STATS_OTHER for all other states. """
        ret = libvirtmod.virConnectGetAllDomainStats(self._o, stats, flags)
        if ret is None:
            raise libvirtError("virConnectGetAllDomainStats() failed", conn=self)

        retlist = list()
        for elem in ret:
            record = (virDomain(self, _obj=elem[0]) , elem[1])
            retlist.append(record)

        return retlist

    def domainListGetStats(self, doms, stats=0, flags=0):
        """ Query statistics for given domains.

        Report statistics of various parameters for a running VM according to @stats
        field. The statistics are returned as an array of structures for each queried
        domain. The structure contains an array of typed parameters containing the
        individual statistics. The typed parameter name for each statistic field
        consists of a dot-separated string containing name of the requested group
        followed by a group specific description of the statistic value.

        The statistic groups are enabled using the @stats parameter which is a
        binary-OR of enum virDomainStatsTypes. The following groups are available
        (although not necessarily implemented for each hypervisor):

        VIR_DOMAIN_STATS_STATE: Return domain state and reason for entering that
        state. The typed parameter keys are in this format:
        "state.state" - state of the VM, returned as int from virDomainState enum
        "state.reason" - reason for entering given state, returned as int from
                         virDomain*Reason enum corresponding to given state.

        Using 0 for @stats returns all stats groups supported by the given
        hypervisor.

        Specifying VIR_CONNECT_GET_ALL_DOMAINS_STATS_ENFORCE_STATS as @flags makes
        the function return error in case some of the stat types in @stats were
        not recognized by the daemon.

        Get statistics about domains provided as a list in @doms. @stats is
        a bit field selecting requested statistics types."""
        domlist = list()
        for dom in doms:
            if not isinstance(dom, virDomain):
                raise libvirtError("domain list contains non-domain elements", conn=self)

            domlist.append(dom._o)

        ret = libvirtmod.virDomainListGetStats(self._o, domlist, stats, flags)
        if ret is None:
            raise libvirtError("virDomainListGetStats() failed", conn=self)

        retlist = list()
        for elem in ret:
            record = (virDomain(self, _obj=elem[0]) , elem[1])
            retlist.append(record)

        return retlist
