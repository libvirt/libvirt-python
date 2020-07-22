#!/usr/bin/env python3
#
# generate python wrappers from the XML API description
#

functions = {}
lxc_functions = {}
qemu_functions = {}
enums = {} # { enumType: { enumConstant: enumValue } }
lxc_enums = {} # { enumType: { enumConstant: enumValue } }
qemu_enums = {} # { enumType: { enumConstant: enumValue } }
event_ids = []
params = [] # [ (paramName, paramValue)... ]

import os
import sys
import string
import re

quiet=True

#######################################################################
#
#  That part if purely the API acquisition phase from the
#  libvirt API description
#
#######################################################################
import os
import xml.sax

debug = 0
onlyOverrides = False

libvirt_headers = [
    "libvirt",
    "libvirt-common",
    "libvirt-domain",
    "libvirt-domain-checkpoint",
    "libvirt-domain-snapshot",
    "libvirt-event",
    "libvirt-host",
    "libvirt-interface",
    "libvirt-network",
    "libvirt-nodedev",
    "libvirt-nwfilter",
    "libvirt-secret",
    "libvirt-storage",
    "libvirt-stream",
]

def getparser():
    # Attach parser to an unmarshalling object. return both objects.
    target = docParser()
    parser = xml.sax.make_parser()
    parser.setContentHandler(target)
    return parser, target

class docParser(xml.sax.handler.ContentHandler):
    def __init__(self):
        self._methodname = None
        self._data = []
        self.in_function = 0

        self.startElement = self.start
        self.endElement = self.end
        self.characters = self.data

    def close(self):
        if debug:
            print("close")

    def getmethodname(self):
        return self._methodname

    def data(self, text):
        if debug:
            print("data %s" % text)
        self._data.append(text)

    def cdata(self, text):
        if debug:
            print("data %s" % text)
        self._data.append(text)

    def start(self, tag, attrs):
        if debug:
            print("start %s, %s" % (tag, attrs))
        if tag == 'function':
            self._data = []
            self.in_function = 1
            self.function = None
            self.function_cond = None
            self.function_args = []
            self.function_descr = None
            self.function_return = None
            self.function_file = None
            self.function_module= None
            if 'name' in attrs.keys():
                self.function = attrs['name']
            if 'file' in attrs.keys():
                self.function_file = attrs['file']
            if 'module' in attrs.keys():
                self.function_module= attrs['module']
        elif tag == 'cond':
            self._data = []
        elif tag == 'info':
            self._data = []
        elif tag == 'arg':
            if self.in_function == 1:
                self.function_arg_name = None
                self.function_arg_type = None
                self.function_arg_info = None
                if 'name' in attrs.keys():
                    self.function_arg_name = attrs['name']
                    if self.function_arg_name == 'from':
                        self.function_arg_name = 'frm'
                if 'type' in attrs.keys():
                    self.function_arg_type = attrs['type']
                if 'info' in attrs.keys():
                    self.function_arg_info = attrs['info']
        elif tag == 'return':
            if self.in_function == 1:
                self.function_return_type = None
                self.function_return_info = None
                self.function_return_field = None
                if 'type' in attrs.keys():
                    self.function_return_type = attrs['type']
                if 'info' in attrs.keys():
                    self.function_return_info = attrs['info']
                if 'field' in attrs.keys():
                    self.function_return_field = attrs['field']
        elif tag == 'enum':
            # enums come from header files, hence virterror.h
            if attrs['file'] in libvirt_headers + ["virerror", "virterror"]:
                enum(attrs['type'],attrs['name'],attrs['value'])
            elif attrs['file'] == "libvirt-lxc":
                lxc_enum(attrs['type'],attrs['name'],attrs['value'])
            elif attrs['file'] == "libvirt-qemu":
                qemu_enum(attrs['type'],attrs['name'],attrs['value'])
        elif tag == "macro":
            if "string" in attrs.keys():
                params.append((attrs['name'], attrs['string']))

    def end(self, tag):
        if debug:
            print("end %s" % tag)
        if tag == 'function':
            # functions come from source files, hence 'virerror.c'
            if self.function is not None:
                if self.function_module in libvirt_headers + \
                            ["event", "virevent", "virerror", "virterror"]:
                    function(self.function, self.function_descr,
                             self.function_return, self.function_args,
                             self.function_file, self.function_module,
                             self.function_cond)
                elif self.function_module == "libvirt-lxc":
                    lxc_function(self.function, self.function_descr,
                             self.function_return, self.function_args,
                             self.function_file, self.function_module,
                             self.function_cond)
                elif self.function_module == "libvirt-qemu":
                    qemu_function(self.function, self.function_descr,
                             self.function_return, self.function_args,
                             self.function_file, self.function_module,
                             self.function_cond)
                elif self.function_file == "python":
                    function(self.function, self.function_descr,
                             self.function_return, self.function_args,
                             self.function_file, self.function_module,
                             self.function_cond)
                elif self.function_file == "python-lxc":
                    lxc_function(self.function, self.function_descr,
                                  self.function_return, self.function_args,
                                  self.function_file, self.function_module,
                                  self.function_cond)
                elif self.function_file == "python-qemu":
                    qemu_function(self.function, self.function_descr,
                                  self.function_return, self.function_args,
                                  self.function_file, self.function_module,
                                  self.function_cond)
                self.in_function = 0
        elif tag == 'arg':
            if self.in_function == 1:
                self.function_args.append([self.function_arg_name,
                                           self.function_arg_type,
                                           self.function_arg_info])
        elif tag == 'return':
            if self.in_function == 1:
                self.function_return = [self.function_return_type,
                                        self.function_return_info,
                                        self.function_return_field]
        elif tag == 'info':
            str = ''
            for c in self._data:
                str = str + c
            if self.in_function == 1:
                self.function_descr = str
        elif tag == 'cond':
            str = ''
            for c in self._data:
                str = str + c
            if self.in_function == 1:
                self.function_cond = str


def function(name, desc, ret, args, file, module, cond):
    global onlyOverrides
    if onlyOverrides and name not in functions:
        return
    if name == "virConnectListDomains":
        name = "virConnectListDomainsID"
    functions[name] = (desc, ret, args, file, module, cond)

def qemu_function(name, desc, ret, args, file, module, cond):
    global onlyOverrides
    if onlyOverrides and name not in qemu_functions:
        return
    qemu_functions[name] = (desc, ret, args, file, module, cond)

def lxc_function(name, desc, ret, args, file, module, cond):
    global onlyOverrides
    if onlyOverrides and name not in lxc_functions:
        return
    lxc_functions[name] = (desc, ret, args, file, module, cond)

def enum(type, name, value):
    if type not in enums:
        enums[type] = {}
    if (name.startswith('VIR_DOMAIN_EVENT_ID_') or
        name.startswith('VIR_NETWORK_EVENT_ID_')):
        event_ids.append(name)
    if value == 'VIR_TYPED_PARAM_INT':
        value = 1
    elif value == 'VIR_TYPED_PARAM_UINT':
        value = 2
    elif value == 'VIR_TYPED_PARAM_LLONG':
        value = 3
    elif value == 'VIR_TYPED_PARAM_ULLONG':
        value = 4
    elif value == 'VIR_TYPED_PARAM_DOUBLE':
        value = 5
    elif value == 'VIR_TYPED_PARAM_BOOLEAN':
        value = 6
    elif value == 'VIR_DOMAIN_AFFECT_CURRENT':
        value = 0
    elif value == 'VIR_DOMAIN_AFFECT_LIVE':
        value = 1
    elif value == 'VIR_DOMAIN_AFFECT_CONFIG':
        value = 2
    if onlyOverrides and name not in enums[type]:
        return
    enums[type][name] = value

def lxc_enum(type, name, value):
    if type not in lxc_enums:
        lxc_enums[type] = {}
    if onlyOverrides and name not in lxc_enums[type]:
        return
    lxc_enums[type][name] = value

def qemu_enum(type, name, value):
    if type not in qemu_enums:
        qemu_enums[type] = {}
    if value == 'VIR_DOMAIN_AGENT_RESPONSE_TIMEOUT_BLOCK':
        value = -2
    elif value == 'VIR_DOMAIN_AGENT_RESPONSE_TIMEOUT_DEFAULT':
        value = -1
    elif value == 'VIR_DOMAIN_AGENT_RESPONSE_TIMEOUT_NOWAIT':
        value = 0
    if onlyOverrides and name not in qemu_enums[type]:
        return
    qemu_enums[type][name] = value


#######################################################################
#
#  Some filtering rules to drop functions/types which should not
#  be exposed as-is on the Python interface
#
#######################################################################

functions_failed = []
lxc_functions_failed = []
qemu_functions_failed = []
functions_skipped = [
    "virConnectListDomains",
]
lxc_functions_skipped = []
qemu_functions_skipped = []

skipped_modules = {
}

skipped_types = {
#    'int *': "usually a return type",
     'virConnectDomainEventCallback': "No function types in python",
     'virConnectDomainEventGenericCallback': "No function types in python",
     'virConnectDomainEventRTCChangeCallback': "No function types in python",
     'virConnectDomainEventWatchdogCallback': "No function types in python",
     'virConnectDomainEventIOErrorCallback': "No function types in python",
     'virConnectDomainEventGraphicsCallback': "No function types in python",
     'virConnectDomainQemuMonitorEventCallback': "No function types in python",
     'virStreamEventCallback': "No function types in python",
     'virEventHandleCallback': "No function types in python",
     'virEventTimeoutCallback': "No function types in python",
     'virDomainBlockJobInfoPtr': "Not implemented yet",
}

#######################################################################
#
#  Table of remapping to/from the python type or class to the C
#  counterpart.
#
#######################################################################

py_types = {
    'void': (None, None, None, None),
    'int':  ('i', None, "int", "int"),
    'long':  ('l', None, "long", "long"),
    'double':  ('d', None, "double", "double"),
    'unsigned int':  ('I', None, "int", "int"),
    'unsigned long':  ('l', None, "long", "long"),
    'long long':  ('L', None, "longlong", "long long"),
    'unsigned long long':  ('L', None, "longlong", "long long"),
    'unsigned char *':  ('z', None, "charPtr", "char *"),
    'char *':  ('z', None, "charPtr", "char *"),
    'const char *':  ('z', None, "constcharPtr", "const char *"),
    'size_t': ('n', None, "size_t", "size_t"),

    'virDomainPtr':  ('O', "virDomain", "virDomainPtr", "virDomainPtr"),
    'virDomain *':  ('O', "virDomain", "virDomainPtr", "virDomainPtr"),
    'const virDomain *':  ('O', "virDomain", "virDomainPtr", "virDomainPtr"),

    'virNetworkPtr':  ('O', "virNetwork", "virNetworkPtr", "virNetworkPtr"),
    'virNetwork *':  ('O', "virNetwork", "virNetworkPtr", "virNetworkPtr"),
    'const virNetwork *':  ('O', "virNetwork", "virNetworkPtr", "virNetworkPtr"),

    'virNetworkPortPtr':  ('O', "virNetworkPort", "virNetworkPortPtr", "virNetworkPortPtr"),
    'virNetworkPort *':  ('O', "virNetworkPort", "virNetworkPortPtr", "virNetworkPortPtr"),
    'const virNetworkPort *':  ('O', "virNetworkPort", "virNetworkPortPtr", "virNetworkPortPtr"),

    'virInterfacePtr':  ('O', "virInterface", "virInterfacePtr", "virInterfacePtr"),
    'virInterface *':  ('O', "virInterface", "virInterfacePtr", "virInterfacePtr"),
    'const virInterface *':  ('O', "virInterface", "virInterfacePtr", "virInterfacePtr"),

    'virStoragePoolPtr':  ('O', "virStoragePool", "virStoragePoolPtr", "virStoragePoolPtr"),
    'virStoragePool *':  ('O', "virStoragePool", "virStoragePoolPtr", "virStoragePoolPtr"),
    'const virStoragePool *':  ('O', "virStoragePool", "virStoragePoolPtr", "virStoragePoolPtr"),

    'virStorageVolPtr':  ('O', "virStorageVol", "virStorageVolPtr", "virStorageVolPtr"),
    'virStorageVol *':  ('O', "virStorageVol", "virStorageVolPtr", "virStorageVolPtr"),
    'const virStorageVol *':  ('O', "virStorageVol", "virStorageVolPtr", "virStorageVolPtr"),

    'virConnectPtr':  ('O', "virConnect", "virConnectPtr", "virConnectPtr"),
    'virConnect *':  ('O', "virConnect", "virConnectPtr", "virConnectPtr"),
    'const virConnect *':  ('O', "virConnect", "virConnectPtr", "virConnectPtr"),

    'virNodeDevicePtr':  ('O', "virNodeDevice", "virNodeDevicePtr", "virNodeDevicePtr"),
    'virNodeDevice *':  ('O', "virNodeDevice", "virNodeDevicePtr", "virNodeDevicePtr"),
    'const virNodeDevice *':  ('O', "virNodeDevice", "virNodeDevicePtr", "virNodeDevicePtr"),

    'virSecretPtr':  ('O', "virSecret", "virSecretPtr", "virSecretPtr"),
    'virSecret *':  ('O', "virSecret", "virSecretPtr", "virSecretPtr"),
    'const virSecret *':  ('O', "virSecret", "virSecretPtr", "virSecretPtr"),

    'virNWFilterPtr':  ('O', "virNWFilter", "virNWFilterPtr", "virNWFilterPtr"),
    'virNWFilter *':  ('O', "virNWFilter", "virNWFilterPtr", "virNWFilterPtr"),
    'const virNWFilter *':  ('O', "virNWFilter", "virNWFilterPtr", "virNWFilterPtr"),

    'virNWFilterBindingPtr':  ('O', "virNWFilterBinding", "virNWFilterBindingPtr", "virNWFilterBindingPtr"),
    'virNWFilterBinding *':  ('O', "virNWFilterBinding", "virNWFilterBindingPtr", "virNWFilterBindingPtr"),
    'const virNWFilterBinding *':  ('O', "virNWFilterBinding", "virNWFilterBindingPtr", "virNWFilterBindingPtr"),

    'virStreamPtr':  ('O', "virStream", "virStreamPtr", "virStreamPtr"),
    'virStream *':  ('O', "virStream", "virStreamPtr", "virStreamPtr"),
    'const virStream *':  ('O', "virStream", "virStreamPtr", "virStreamPtr"),

    'virDomainCheckpointPtr':  ('O', "virDomainCheckpoint", "virDomainCheckpointPtr", "virDomainCheckpointPtr"),
    'virDomainCheckpoint *':  ('O', "virDomainCheckpoint", "virDomainCheckpointPtr", "virDomainCheckpointPtr"),
    'const virDomainCheckpoint *':  ('O', "virDomainCheckpoint", "virDomainCheckpointPtr", "virDomainCheckpointPtr"),

    'virDomainSnapshotPtr':  ('O', "virDomainSnapshot", "virDomainSnapshotPtr", "virDomainSnapshotPtr"),
    'virDomainSnapshot *':  ('O', "virDomainSnapshot", "virDomainSnapshotPtr", "virDomainSnapshotPtr"),
    'const virDomainSnapshot *':  ('O', "virDomainSnapshot", "virDomainSnapshotPtr", "virDomainSnapshotPtr"),
}

unknown_types = {}

#######################################################################
#
#  This part writes the C <-> Python stubs libvirt.[ch] and
#  the table libvirt-export.c to add when registering the Python module
#
#######################################################################

# Class methods which are written by hand in libvirt.c but the Python-level
# code is still automatically generated (so they are not in skip_function()).
skip_impl = (
    'virConnectGetVersion',
    'virConnectGetLibVersion',
    'virConnectListDomainsID',
    'virConnectListDefinedDomains',
    'virConnectListNetworks',
    'virConnectListDefinedNetworks',
    'virConnectListSecrets',
    'virConnectListInterfaces',
    'virConnectListStoragePools',
    'virConnectListDefinedStoragePools',
    'virConnectListStorageVols',
    'virConnectListDefinedStorageVols',
    'virConnectListDefinedInterfaces',
    'virConnectListNWFilters',
    'virDomainSnapshotListNames',
    'virDomainSnapshotListChildrenNames',
    'virConnGetLastError',
    'virGetLastError',
    'virDomainGetInfo',
    'virDomainGetState',
    'virDomainGetControlInfo',
    'virDomainGetBlockInfo',
    'virDomainGetJobInfo',
    'virDomainGetJobStats',
    'virNodeGetInfo',
    'virNodeGetSecurityModel',
    'virDomainGetSecurityLabel',
    'virDomainGetSecurityLabelList',
    'virDomainGetUUID',
    'virDomainGetUUIDString',
    'virDomainLookupByUUID',
    'virNetworkGetUUID',
    'virNetworkGetUUIDString',
    'virNetworkLookupByUUID',
    'virNetworkPortGetUUID',
    'virNetworkPortGetUUIDString',
    'virNetworkPortLookupByUUID',
    'virDomainGetAutostart',
    'virNetworkGetAutostart',
    'virDomainBlockStats',
    'virDomainInterfaceStats',
    'virDomainMemoryStats',
    'virNodeGetCellsFreeMemory',
    'virDomainGetSchedulerType',
    'virDomainGetSchedulerParameters',
    'virDomainGetSchedulerParametersFlags',
    'virDomainSetSchedulerParameters',
    'virDomainSetSchedulerParametersFlags',
    'virDomainSetBlkioParameters',
    'virDomainGetBlkioParameters',
    'virDomainSetMemoryParameters',
    'virDomainGetMemoryParameters',
    'virDomainSetNumaParameters',
    'virDomainGetNumaParameters',
    'virDomainGetVcpus',
    'virDomainPinVcpu',
    'virDomainPinVcpuFlags',
    'virDomainGetVcpuPinInfo',
    'virDomainGetEmulatorPinInfo',
    'virDomainPinEmulator',
    'virDomainGetIOThreadInfo',
    'virDomainPinIOThread',
    'virDomainSetIOThreadParams',
    'virSecretGetValue',
    'virSecretSetValue',
    'virSecretGetUUID',
    'virSecretGetUUIDString',
    'virSecretLookupByUUID',
    'virNWFilterGetUUID',
    'virNWFilterGetUUIDString',
    'virNWFilterLookupByUUID',
    'virStoragePoolGetUUID',
    'virStoragePoolGetUUIDString',
    'virStoragePoolLookupByUUID',
    'virStoragePoolGetInfo',
    'virStorageVolGetInfo',
    'virStorageVolGetInfoFlags',
    'virStoragePoolGetAutostart',
    'virStoragePoolListVolumes',
    'virDomainBlockPeek',
    'virDomainMemoryPeek',
    'virEventRegisterImpl',
    'virNodeListDevices',
    'virNodeDeviceListCaps',
    'virConnectBaselineCPU',
    'virDomainRevertToSnapshot',
    'virDomainSendKey',
    'virNodeGetCPUStats',
    'virNodeGetMemoryStats',
    'virDomainGetBlockJobInfo',
    'virDomainMigrateGetCompressionCache',
    'virDomainMigrateGetMaxSpeed',
    'virDomainMigrateGetMaxDowntime',
    'virDomainBlockStatsFlags',
    'virDomainSetBlockIoTune',
    'virDomainGetBlockIoTune',
    'virDomainSetInterfaceParameters',
    'virDomainGetInterfaceParameters',
    'virDomainGetCPUStats',
    'virDomainGetDiskErrors',
    'virNodeGetMemoryParameters',
    'virNodeSetMemoryParameters',
    'virConnectSetIdentity',
    'virNodeGetCPUMap',
    'virDomainMigrate3',
    'virDomainMigrateToURI3',
    'virConnectGetCPUModelNames',
    'virNodeGetFreePages',
    'virNetworkGetDHCPLeases',
    'virDomainBlockCopy',
    'virNodeAllocPages',
    'virDomainGetFSInfo',
    'virDomainInterfaceAddresses',
    'virDomainGetPerfEvents',
    'virDomainSetPerfEvents',
    'virDomainGetGuestVcpus',
    'virConnectBaselineHypervisorCPU',
    'virDomainGetLaunchSecurityInfo',
    'virNodeGetSEVInfo',
    'virNetworkPortGetParameters',
    'virNetworkPortSetParameters',
    'virDomainGetGuestInfo',
)

lxc_skip_impl = (
    'virDomainLxcOpenNamespace',
)

qemu_skip_impl = (
    'virDomainQemuMonitorCommand',
    'virDomainQemuAgentCommand',
)


# These are functions which the generator skips completely - no python
# or C code is generated. Generally should not be used for any more
# functions than those already listed
skip_function = (
    'virConnectListDomains', # Python API is called virConnectListDomainsID for unknown reasons
    'virConnSetErrorFunc', # Not used in Python API  XXX is this a bug ?
    'virResetError', # Not used in Python API  XXX is this a bug ?
    'virGetVersion', # Python C code is manually written
    'virSetErrorFunc', # Python API is called virRegisterErrorHandler for unknown reasons
    'virConnCopyLastError', # Python API is called virConnGetLastError instead
    'virCopyLastError', # Python API is called virGetLastError instead
    'virConnectOpenAuth', # Python C code is manually written
    'virDefaultErrorFunc', # Python virErrorFuncHandler impl calls this from C
    'virConnectDomainEventRegister',   # overridden in virConnect.py
    'virConnectDomainEventDeregister', # overridden in virConnect.py
    'virConnectDomainEventRegisterAny',   # overridden in virConnect.py
    'virConnectDomainEventDeregisterAny', # overridden in virConnect.py
    'virConnectNetworkEventRegisterAny',   # overridden in virConnect.py
    'virConnectNetworkEventDeregisterAny', # overridden in virConnect.py
    'virConnectStoragePoolEventRegisterAny',   # overridden in virConnect.py
    'virConnectStoragePoolEventDeregisterAny', # overridden in virConnect.py
    'virConnectNodeDeviceEventRegisterAny',   # overridden in virConnect.py
    'virConnectNodeDeviceEventDeregisterAny', # overridden in virConnect.py
    'virConnectSecretEventRegisterAny',   # overridden in virConnect.py
    'virConnectSecretEventDeregisterAny', # overridden in virConnect.py
    'virSaveLastError', # We have our own python error wrapper
    'virFreeError', # Only needed if we use virSaveLastError
    'virConnectListAllDomains', # overridden in virConnect.py
    'virDomainListAllCheckpoints', # overridden in virDomain.py
    'virDomainCheckpointListAllChildren', # overridden in virDomainCheckpoint.py
    'virDomainListAllSnapshots', # overridden in virDomain.py
    'virDomainSnapshotListAllChildren', # overridden in virDomainSnapshot.py
    'virConnectListAllStoragePools', # overridden in virConnect.py
    'virStoragePoolListAllVolumes', # overridden in virStoragePool.py
    'virConnectListAllNetworks', # overridden in virConnect.py
    'virNetworkListAllPorts', # overridden in virConnect.py
    'virConnectListAllInterfaces', # overridden in virConnect.py
    'virConnectListAllNodeDevices', # overridden in virConnect.py
    'virConnectListAllNWFilters', # overridden in virConnect.py
    'virConnectListAllNWFilterBindings', # overridden in virConnect.py
    'virConnectListAllSecrets', # overridden in virConnect.py
    'virConnectGetAllDomainStats', # overridden in virConnect.py
    'virDomainListGetStats', # overridden in virConnect.py

    'virStreamRecvAll', # Pure python libvirt-override-virStream.py
    'virStreamSendAll', # Pure python libvirt-override-virStream.py
    'virStreamRecv', # overridden in libvirt-override-virStream.py
    'virStreamSend', # overridden in libvirt-override-virStream.py
    'virStreamRecvHole', # overridden in libvirt-override-virStream.py
    'virStreamSendHole', # overridden in libvirt-override-virStream.py
    'virStreamRecvFlags', # overridden in libvirt-override-virStream.py
    'virStreamSparseRecvAll', # overridden in libvirt-override-virStream.py
    'virStreamSparseSendAll', # overridden in libvirt-override-virStream.py

    'virConnectUnregisterCloseCallback', # overridden in virConnect.py
    'virConnectRegisterCloseCallback', # overridden in virConnect.py

    'virDomainCreateXMLWithFiles', # overridden in virConnect.py
    'virDomainCreateWithFiles', # overridden in virDomain.py

    'virDomainFSFreeze', # overridden in virDomain.py
    'virDomainFSThaw', # overridden in virDomain.py
    'virDomainGetTime', # overridden in virDomain.py
    'virDomainSetTime', # overridden in virDomain.py

    # 'Ref' functions have no use for bindings users.
    "virConnectRef",
    "virDomainRef",
    "virInterfaceRef",
    "virNetworkRef",
    "virNetworkPortRef",
    "virNodeDeviceRef",
    "virSecretRef",
    "virNWFilterRef",
    "virNWFilterBindingRef",
    "virStoragePoolRef",
    "virStorageVolRef",
    "virStreamRef",
    "virDomainCheckpointRef",
    "virDomainSnapshotRef",

    # This functions shouldn't be called via the bindings (and even the docs
    # contain an explicit warning to that effect). The equivalent should be
    # implemented in pure python for each class
    "virDomainGetConnect",
    "virInterfaceGetConnect",
    "virNetworkGetConnect",
    "virNetworkPortGetNetwork",
    "virSecretGetConnect",
    "virNWFilterGetConnect",
    "virStoragePoolGetConnect",
    "virStorageVolGetConnect",
    "virDomainCheckpointGetConnect",
    "virDomainCheckpointGetDomain",
    "virDomainSnapshotGetConnect",
    "virDomainSnapshotGetDomain",

    # only useful in C code, python code uses dict for typed parameters
    "virTypedParamsAddBoolean",
    "virTypedParamsAddDouble",
    "virTypedParamsAddFromString",
    "virTypedParamsAddInt",
    "virTypedParamsAddLLong",
    "virTypedParamsAddString",
    "virTypedParamsAddUInt",
    "virTypedParamsAddULLong",
    "virTypedParamsClear",
    "virTypedParamsFree",
    "virTypedParamsGet",
    "virTypedParamsGetBoolean",
    "virTypedParamsGetDouble",
    "virTypedParamsGetInt",
    "virTypedParamsGetLLong",
    "virTypedParamsGetString",
    "virTypedParamsGetUInt",
    "virTypedParamsGetULLong",

    'virNetworkDHCPLeaseFree', # only useful in C, python code uses list
    'virDomainStatsRecordListFree', # only useful in C, python uses dict
    'virDomainFSInfoFree', # only useful in C, python code uses list
    'virDomainIOThreadInfoFree', # only useful in C, python code uses list
    'virDomainInterfaceFree', # only useful in C, python code uses list
)

lxc_skip_function = (
  "virDomainLxcEnterNamespace",
  "virDomainLxcEnterSecurityLabel",
)
qemu_skip_function = (
    #"virDomainQemuAttach",
    'virConnectDomainQemuMonitorEventRegister', # overridden in -qemu.py
    'virConnectDomainQemuMonitorEventDeregister', # overridden in -qemu.py
)

# Generate C code, but skip python impl
function_skip_python_impl = (
    "virStreamFree", # Needed in custom virStream __del__, but free shouldn't
                     # be exposed in bindings
)

lxc_function_skip_python_impl = ()
qemu_function_skip_python_impl = ()

function_skip_index_one = (
    "virDomainRevertToSnapshot",
)

def print_function_wrapper(module, name, output, export, include):
    global py_types
    global unknown_types
    global functions
    global lxc_functions
    global qemu_functions
    global skipped_modules
    global function_skip_python_impl

    try:
        if module == "libvirt":
            (desc, ret, args, file, mod, cond) = functions[name]
        if module == "libvirt-lxc":
            (desc, ret, args, file, mod, cond) = lxc_functions[name]
        if module == "libvirt-qemu":
            (desc, ret, args, file, mod, cond) = qemu_functions[name]
    except:
        print("failed to get function %s infos" % name)
        return

    if module in skipped_modules:
        return 0

    if module == "libvirt":
        if name in skip_function:
            return 0
        if name in skip_impl:
            # Don't delete the function entry in the caller.
            return 1
    elif module == "libvirt-lxc":
        if name in lxc_skip_function:
            return 0
        if name in lxc_skip_impl:
            # Don't delete the function entry in the caller.
            return 1
    elif module == "libvirt-qemu":
        if name in qemu_skip_function:
            return 0
        if name in qemu_skip_impl:
            # Don't delete the function entry in the caller.
            return 1

    c_call = ""
    format=""
    format_args=""
    c_args=""
    c_return=""
    c_convert=""
    num_bufs=0
    for arg in args:
        # This should be correct
        if arg[1][0:6] == "const ":
            arg[1] = arg[1][6:]
        c_args = c_args + "    %s %s;\n" % (arg[1], arg[0])
        if arg[1] in py_types:
            (f, t, n, c) = py_types[arg[1]]
            if f is not None:
                format = format + f
            if t is not None:
                format_args = format_args + ", &pyobj_%s" % (arg[0])
                c_args = c_args + "    PyObject *pyobj_%s;\n" % (arg[0])
                c_convert = c_convert + \
                   "    %s = (%s) Py%s_Get(pyobj_%s);\n" % (arg[0],
                   arg[1], t, arg[0])
            else:
                format_args = format_args + ", &%s" % (arg[0])
            if f == 't#':
                format_args = format_args + ", &py_buffsize%d" % num_bufs
                c_args = c_args + "    int py_buffsize%d;\n" % num_bufs
                num_bufs = num_bufs + 1
            if c_call != "":
                c_call = c_call + ", "
            c_call = c_call + "%s" % (arg[0])
        else:
            if arg[1] in skipped_types:
                return 0
            if arg[1] in unknown_types:
                lst = unknown_types[arg[1]]
                lst.append(name)
            else:
                unknown_types[arg[1]] = [name]
            return -1
    if format != "":
        format = format + ":%s" % (name)

    if ret[0] == 'void':
        if file == "python_accessor":
            if args[1][1] == "char *":
                c_call = "\n    VIR_FREE(%s->%s);\n" % (
                                 args[0][0], args[1][0])
                c_call = c_call + "    %s->%s = (%s)strdup((const xmlChar *)%s);\n" % (args[0][0],
                                 args[1][0], args[1][1], args[1][0])
            else:
                c_call = "\n    %s->%s = %s;\n" % (args[0][0], args[1][0],
                                                   args[1][0])
        else:
            c_call = "\n    %s(%s);\n" % (name, c_call)
        ret_convert = "    Py_INCREF(Py_None);\n    return Py_None;\n"
    elif ret[0] in py_types:
        (f, t, n, c) = py_types[ret[0]]
        c_return = "    %s c_retval;\n" % (ret[0])
        if file == "python_accessor" and ret[2] is not None:
            c_call = "\n    c_retval = %s->%s;\n" % (args[0][0], ret[2])
        else:
            c_call = "\n    c_retval = %s(%s);\n" % (name, c_call)
        ret_convert = "    py_retval = libvirt_%sWrap((%s) c_retval);\n" % (n,c)
        if n == "charPtr":
            ret_convert = ret_convert + "    free(c_retval);\n"
        ret_convert = ret_convert + "    return py_retval;\n"
    else:
        if ret[0] in skipped_types:
            return 0
        if ret[0] in unknown_types:
            lst = unknown_types[ret[0]]
            lst.append(name)
        else:
            unknown_types[ret[0]] = [name]
        return -1

    if cond is not None and cond != "":
        include.write("#if %s\n" % cond)
        export.write("#if %s\n" % cond)
        output.write("#if %s\n" % cond)

    include.write("PyObject * ")
    if module == "libvirt":
        include.write("libvirt_%s(PyObject *self, PyObject *args);\n" % (name))
        export.write("    { (char *)\"%s\", libvirt_%s, METH_VARARGS, NULL },\n" %
                     (name, name))
    elif module == "libvirt-lxc":
        include.write("libvirt_lxc_%s(PyObject *self, PyObject *args);\n" % (name))
        export.write("    { (char *)\"%s\", libvirt_lxc_%s, METH_VARARGS, NULL },\n" %
                     (name, name))
    elif module == "libvirt-qemu":
        include.write("libvirt_qemu_%s(PyObject *self, PyObject *args);\n" % (name))
        export.write("    { (char *)\"%s\", libvirt_qemu_%s, METH_VARARGS, NULL },\n" %
                     (name, name))

    if file == "python":
        # Those have been manually generated
        if cond is not None and cond != "":
            include.write("#endif\n")
            export.write("#endif\n")
            output.write("#endif\n")
        return 1
    if file == "python_accessor" and ret[0] != "void" and ret[2] is None:
        # Those have been manually generated
        if cond is not None and cond != "":
            include.write("#endif\n")
            export.write("#endif\n")
            output.write("#endif\n")
        return 1

    output.write("PyObject *\n")
    if module == "libvirt":
        output.write("libvirt_%s(PyObject *self ATTRIBUTE_UNUSED," % (name))
    elif module == "libvirt-lxc":
        output.write("libvirt_lxc_%s(PyObject *self ATTRIBUTE_UNUSED," % (name))
    elif module == "libvirt-qemu":
        output.write("libvirt_qemu_%s(PyObject *self ATTRIBUTE_UNUSED," % (name))
    output.write(" PyObject *args")
    if format == "":
        output.write(" ATTRIBUTE_UNUSED")
    output.write(") {\n")
    if ret[0] != 'void':
        output.write("    PyObject *py_retval;\n")
    if c_return != "":
        output.write(c_return)
    if c_args != "":
        output.write(c_args)
    if format != "":
        output.write("\n    if (!PyArg_ParseTuple(args, (char *)\"%s\"%s))\n" %
                     (format, format_args))
        output.write("        return NULL;\n")
    if c_convert != "":
        output.write(c_convert + "\n")

    output.write("    LIBVIRT_BEGIN_ALLOW_THREADS;")
    output.write(c_call)
    output.write("    LIBVIRT_END_ALLOW_THREADS;\n")
    output.write(ret_convert)
    output.write("}\n\n")
    if cond is not None and cond != "":
        include.write("#endif /* %s */\n" % cond)
        export.write("#endif /* %s */\n" % cond)
        output.write("#endif /* %s */\n" % cond)

    if module == "libvirt":
        if name in function_skip_python_impl:
            return 0
    elif module == "libvirt-lxc":
        if name in lxc_function_skip_python_impl:
            return 0
    elif module == "libvirt-qemu":
        if name in qemu_function_skip_python_impl:
            return 0
    return 1

def print_c_pointer(classname, output, export, include):
    output.write("PyObject *\n")
    output.write("libvirt_%s_pointer(PyObject *self ATTRIBUTE_UNUSED, PyObject *args)\n" % classname)
    output.write("{\n")
    output.write("    %sPtr ptr;\n" % classname)
    output.write("    PyObject *pyptr;\n")
    output.write("    PyObject *pylong;\n")
    output.write("\n")
    output.write("    if (!PyArg_ParseTuple(args, (char *) \"O\", &pyptr))\n")
    output.write("        return NULL;\n")
    output.write("    ptr = (%sPtr) Py%s_Get(pyptr);\n" % (classname, classname))
    output.write("    pylong = PyLong_FromVoidPtr(ptr);\n")
    output.write("    return pylong;\n")
    output.write("}\n")
    output.write("\n")

    include.write("PyObject *libvirt_%s_pointer(PyObject *self, PyObject *args);\n" % classname)

    export.write("    { (char *)\"%s_pointer\", libvirt_%s_pointer, METH_VARARGS, NULL },\n" %
                 (classname, classname))

def buildStubs(module, api_xml):
    global py_types
    global unknown_types
    global onlyOverrides

    if module not in ["libvirt", "libvirt-qemu", "libvirt-lxc"]:
        print("ERROR: Unknown module type: %s" % module)
        return None

    if module == "libvirt":
        funcs = functions
        funcs_failed = functions_failed
        funcs_skipped = functions_skipped
    elif module == "libvirt-lxc":
        funcs = lxc_functions
        funcs_failed = lxc_functions_failed
        funcs_skipped = lxc_functions_skipped
    elif module == "libvirt-qemu":
        funcs = qemu_functions
        funcs_failed = qemu_functions_failed
        funcs_skipped = qemu_functions_skipped

    try:
        f = open(api_xml)
        data = f.read()
        f.close()
        onlyOverrides = False
        (parser, target)  = getparser()
        parser.feed(data)
        parser.close()
    except IOError:
        msg = sys.exc_info()[1]
        print(api_xml, ":", msg)
        sys.exit(1)

    n = len(list(funcs.keys()))
    if not quiet:
        print("Found %d functions in %s" % ((n), api_xml))

    override_api_xml = "%s-override-api.xml" % module
    py_types['pythonObject'] = ('O', "pythonObject", "pythonObject", "pythonObject")

    try:
        f = open(override_api_xml)
        data = f.read()
        f.close()
        onlyOverrides = True
        (parser, target)  = getparser()
        parser.feed(data)
        parser.close()
    except IOError:
        msg = sys.exc_info()[1]
        print(override_api_xml, ":", msg)

    if not quiet:
        # XXX: This is not right, same function already in @functions
        # will be overwritten.
        print("Found %d functions in %s" % ((len(list(funcs.keys())) - n), override_api_xml))
    nb_wrap = 0
    failed = 0
    skipped = 0

    header_file = "build/%s.h" % module
    export_file = "build/%s-export.c" % module
    wrapper_file = "build/%s.c" % module

    include = open(header_file, "w")
    include.write("/* Generated by generator.py */\n\n")

    export = open(export_file, "w")
    export.write("/* Generated by generator.py */\n\n")

    wrapper = open(wrapper_file, "w")
    wrapper.write("/* Generated by generator.py */\n\n")
    wrapper.write("#include <Python.h>\n")
    wrapper.write("#include <libvirt/" + module + ".h>\n")
    wrapper.write("#include \"typewrappers.h\"\n")
    wrapper.write("#include \"build/" + module + ".h\"\n\n")

    for function in sorted(funcs.keys()):
        # Skip the functions which are not for the module
        ret = print_function_wrapper(module, function, wrapper, export, include)
        if ret < 0:
            failed = failed + 1
            funcs_failed.append(function)
            del funcs[function]
        if ret == 0:
            skipped = skipped + 1
            funcs_skipped.append(function)
            del funcs[function]
        if ret == 1:
            nb_wrap = nb_wrap + 1

    if module == "libvirt":
        # Write C pointer conversion functions.
        for classname in primary_classes:
            print_c_pointer(classname, wrapper, export, include)
        # Write define wrappers around event id enums, so that the
        # preprocessor can see which enums were available.
        for event_id in event_ids:
            include.write("#define %s %s\n" % (event_id, event_id))

    include.close()
    export.close()
    wrapper.close()

    if not quiet:
        print("Generated %d wrapper functions" % nb_wrap)

    if unknown_types:
        print("Missing type converters: ")
        for type in list(unknown_types.keys()):
            print("%s:%d " % (type, len(unknown_types[type])))

    for f in funcs_failed:
        print("ERROR: failed %s" % f)

    if failed > 0:
        return -1
    if len(unknown_types) > 0:
        return -1
    return 0

#######################################################################
#
#  This part writes part of the Python front-end classes based on
#  mapping rules between types and classes and also based on function
#  renaming to get consistent function names at the Python level
#
#######################################################################

#
# The type automatically remapped to generated classes
#
classes_type = {
    "virDomainPtr": ("._o", "virDomain(self,_obj=%s)", "virDomain"),
    "virDomain *": ("._o", "virDomain(self, _obj=%s)", "virDomain"),
    "virNetworkPtr": ("._o", "virNetwork(self, _obj=%s)", "virNetwork"),
    "virNetwork *": ("._o", "virNetwork(self, _obj=%s)", "virNetwork"),
    "virNetworkPortPtr": ("._o", "virNetworkPort(self, _obj=%s)", "virNetworkPort"),
    "virNetworkPort *": ("._o", "virNetworkPort(self, _obj=%s)", "virNetworkPort"),
    "virInterfacePtr": ("._o", "virInterface(self, _obj=%s)", "virInterface"),
    "virInterface *": ("._o", "virInterface(self, _obj=%s)", "virInterface"),
    "virStoragePoolPtr": ("._o", "virStoragePool(self, _obj=%s)", "virStoragePool"),
    "virStoragePool *": ("._o", "virStoragePool(self, _obj=%s)", "virStoragePool"),
    "virStorageVolPtr": ("._o", "virStorageVol(self, _obj=%s)", "virStorageVol"),
    "virStorageVol *": ("._o", "virStorageVol(self, _obj=%s)", "virStorageVol"),
    "virNodeDevicePtr": ("._o", "virNodeDevice(self, _obj=%s)", "virNodeDevice"),
    "virNodeDevice *": ("._o", "virNodeDevice(self, _obj=%s)", "virNodeDevice"),
    "virSecretPtr": ("._o", "virSecret(self, _obj=%s)", "virSecret"),
    "virSecret *": ("._o", "virSecret(self, _obj=%s)", "virSecret"),
    "virNWFilterPtr": ("._o", "virNWFilter(self, _obj=%s)", "virNWFilter"),
    "virNWFilter *": ("._o", "virNWFilter(self, _obj=%s)", "virNWFilter"),
    "virNWFilterBindingPtr": ("._o", "virNWFilterBinding(self, _obj=%s)", "virNWFilterBinding"),
    "virNWFilterBinding *": ("._o", "virNWFilterBinding(self, _obj=%s)", "virNWFilterBinding"),
    "virStreamPtr": ("._o", "virStream(self, _obj=%s)", "virStream"),
    "virStream *": ("._o", "virStream(self, _obj=%s)", "virStream"),
    "virConnectPtr": ("._o", "virConnect(_obj=%s)", "virConnect"),
    "virConnect *": ("._o", "virConnect(_obj=%s)", "virConnect"),
    "virDomainCheckpointPtr": ("._o", "virDomainCheckpoint(self,_obj=%s)", "virDomainCheckpoint"),
    "virDomainCheckpoint *": ("._o", "virDomainCheckpoint(self, _obj=%s)", "virDomainCheckpoint"),
    "virDomainSnapshotPtr": ("._o", "virDomainSnapshot(self,_obj=%s)", "virDomainSnapshot"),
    "virDomainSnapshot *": ("._o", "virDomainSnapshot(self, _obj=%s)", "virDomainSnapshot"),
}

primary_classes = ["virDomain", "virNetwork", "virNetworkPort",
                   "virInterface", "virStoragePool", "virStorageVol",
                   "virConnect", "virNodeDevice", "virSecret",
                   "virNWFilter", "virNWFilterBinding",
                   "virStream", "virDomainCheckpoint", "virDomainSnapshot"]

classes_destructors = {
    "virDomain": "virDomainFree",
    "virNetwork": "virNetworkFree",
    "virNetworkPort": "virNetworkPortFree",
    "virInterface": "virInterfaceFree",
    "virStoragePool": "virStoragePoolFree",
    "virStorageVol": "virStorageVolFree",
    "virNodeDevice" : "virNodeDeviceFree",
    "virSecret": "virSecretFree",
    "virNWFilter": "virNWFilterFree",
    "virNWFilterBinding": "virNWFilterBindingFree",
    "virDomainCheckpoint": "virDomainCheckpointFree",
    "virDomainSnapshot": "virDomainSnapshotFree",
    # We hand-craft __del__ for this one
    #"virStream": "virStreamFree",
}

class_skip_connect_impl = {
    "virConnect" : True,
}

class_domain_impl = {
    "virDomainCheckpoint": True,
    "virDomainSnapshot": True,
}

class_network_impl = {
    "virNetworkPort": True,
}

functions_noexcept = {
    'virDomainGetID': True,
    'virDomainGetName': True,
    'virNetworkGetName': True,
    'virInterfaceGetName': True,
    'virStoragePoolGetName': True,
    'virStorageVolGetName': True,
    'virStorageVolGetkey': True,
    'virNodeDeviceGetName': True,
    'virNodeDeviceGetParent': True,
    'virSecretGetUsageType': True,
    'virSecretGetUsageID': True,
    'virNWFilterGetName': True,
    'virNWFilterBindingGetFilterName': True,
    'virNWFilterBindingGetPortDev': True,
}

function_classes = {}

function_classes["None"] = []

# Functions returning an integral type which need special rules to
# check for errors and raise exceptions.
functions_int_exception_test = {
    'virDomainGetMaxMemory': "%s == 0",
}
functions_int_default_test = "%s == -1"

def is_integral_type (name):
    return not re.search ("^(unsigned)? ?(int|long)$", name) is None

def is_optional_arg(info):
    return re.search("^\(?optional\)?", info) is not None

def is_python_noninteger_type (name):

    return name[-1:] == "*"

def nameFixup(name, classe, type, file):
    # avoid a disastrous clash
    listname = classe + "List"
    ll = len(listname)
    l = len(classe)
    if name[0:l] == listname:
        func = name[l:]
        func = func[0:1].lower() + func[1:]
    elif name[0:16] == "virNetworkDefine":
        func = name[3:]
        func = func[0:1].lower() + func[1:]
    elif name[0:19] == "virNetworkCreateXML":
        func = name[3:]
        func = func[0:1].lower() + func[1:]
    elif name[0:16] == "virNetworkLookup":
        func = name[3:]
        func = func[0:1].lower() + func[1:]
    elif name[0:23] == "virNetworkPortCreateXML":
        func = name[10:]
        func = func[0:1].lower() + func[1:]
    elif name[0:20] == "virNetworkPortLookup":
        func = name[10:]
        func = func[0:1].lower() + func[1:]
    elif name[0:18] == "virInterfaceDefine":
        func = name[3:]
        func = func[0:1].lower() + func[1:]
    elif name[0:21] == "virInterfaceCreateXML":
        func = name[3:]
        func = func[0:1].lower() + func[1:]
    elif name[0:18] == "virInterfaceLookup":
        func = name[3:]
        func = func[0:1].lower() + func[1:]
    elif name[0:15] == "virSecretDefine":
        func = name[3:]
        func = func[0:1].lower() + func[1:]
    elif name[0:15] == "virSecretLookup":
        func = name[3:]
        func = func[0:1].lower() + func[1:]
    elif name[0:27] == "virNWFilterBindingCreateXML":
        func = name[3:]
        func = func[0:3].lower() + func[3:]
    elif name[0:24] == "virNWFilterBindingLookup":
        func = name[3:]
        func = func[0:3].lower() + func[3:]
    elif name[0:24] == "virNWFilterBindingDefine":
        func = name[3:]
        func = func[0:3].lower() + func[3:]
    elif name[0:24] == "virNWFilterBindingLookup":
        func = name[3:]
        func = func[0:3].lower() + func[3:]
    elif name[0:17] == "virNWFilterDefine":
        func = name[3:]
        func = func[0:3].lower() + func[3:]
    elif name[0:17] == "virNWFilterLookup":
        func = name[3:]
        func = func[0:3].lower() + func[3:]
    elif name[0:20] == "virStoragePoolDefine":
        func = name[3:]
        func = func[0:1].lower() + func[1:]
    elif name[0:23] == "virStoragePoolCreateXML":
        func = name[3:]
        func = func[0:1].lower() + func[1:]
    elif name[0:20] == "virStoragePoolLookup":
        func = name[3:]
        func = func[0:1].lower() + func[1:]
    elif name[0:19] == "virStorageVolDefine":
        func = name[3:]
        func = func[0:1].lower() + func[1:]
    elif name[0:19] == "virStorageVolLookup":
        func = name[3:]
        func = func[0:1].lower() + func[1:]
    elif name[0:20] == "virDomainGetCPUStats":
        func = name[9:]
        func = func[0:1].lower() + func[1:]
    elif name[0:24] == "virDomainGetIOThreadInfo":
        func = name[12:]
        func = func[0:2].lower() + func[2:]
    elif name[0:18] == "virDomainGetFSInfo":
        func = name[12:]
        func = func[0:2].lower() + func[2:]
    elif name[0:12] == "virDomainGet":
        func = name[12:]
        func = func[0:1].lower() + func[1:]
    elif name[0:31] == "virDomainCheckpointLookupByName":
        func = name[9:]
        func = func[0:1].lower() + func[1:]
    elif name[0:28] == "virDomainCheckpointCreateXML":
        func = name[9:]
        func = func[0:1].lower() + func[1:]
    elif name[0:19] == "virDomainCheckpoint":
        func = name[19:]
        func = func[0:1].lower() + func[1:]
    elif name[0:29] == "virDomainSnapshotLookupByName":
        func = name[9:]
        func = func[0:1].lower() + func[1:]
    elif name[0:26] == "virDomainSnapshotListNames":
        func = name[9:]
        func = func[0:1].lower() + func[1:]
    elif name[0:28] == "virDomainSnapshotNumChildren":
        func = name[17:]
        func = func[0:1].lower() + func[1:]
    elif name[0:20] == "virDomainSnapshotNum":
        func = name[9:]
        func = func[0:1].lower() + func[1:]
    elif name[0:26] == "virDomainSnapshotCreateXML":
        func = name[9:]
        func = func[0:1].lower() + func[1:]
    elif name[0:24] == "virDomainSnapshotCurrent":
        func = name[9:]
        func = func[0:1].lower() + func[1:]
    elif name[0:17] == "virDomainSnapshot":
        func = name[17:]
        func = func[0:1].lower() + func[1:]
    elif name[0:9] == "virDomain":
        func = name[9:]
        func = func[0:1].lower() + func[1:]
    elif name[0:17] == "virNetworkPortGet":
        func = name[17:]
        func = func[0:1].lower() + func[1:]
    elif name[0:13] == "virNetworkGet":
        func = name[13:]
        func = func[0:1].lower() + func[1:]
        func = func.replace("dHCP", "DHCP")
    elif name[0:14] == "virNetworkPort":
        func = name[14:]
        func = func[0:1].lower() + func[1:]
    elif name[0:10] == "virNetwork":
        func = name[10:]
        func = func[0:1].lower() + func[1:]
    elif name[0:15] == "virInterfaceGet":
        func = name[15:]
        func = func[0:1].lower() + func[1:]
    elif name[0:12] == "virInterface":
        func = name[12:]
        func = func[0:1].lower() + func[1:]
    elif name[0:12] == 'virSecretGet':
        func = name[12:]
        func = func[0:1].lower() + func[1:]
    elif name[0:9] == 'virSecret':
        func = name[9:]
        func = func[0:1].lower() + func[1:]
    elif name[0:21] == 'virNWFilterBindingGet':
        func = name[21:]
        func = func[0:1].lower() + func[1:]
    elif name[0:18] == 'virNWFilterBinding':
        func = name[18:]
        func = func[0:1].lower() + func[1:]
    elif name[0:14] == 'virNWFilterGet':
        func = name[14:]
        func = func[0:1].lower() + func[1:]
    elif name[0:11] == 'virNWFilter':
        func = name[11:]
        func = func[0:1].lower() + func[1:]
    elif name[0:12] == 'virStreamNew':
        func = "newStream"
    elif name[0:9] == 'virStream':
        func = name[9:]
        func = func[0:1].lower() + func[1:]
    elif name[0:17] == "virStoragePoolGet":
        func = name[17:]
        func = func[0:1].lower() + func[1:]
    elif name[0:14] == "virStoragePool":
        func = name[14:]
        func = func[0:1].lower() + func[1:]
    elif name[0:16] == "virStorageVolGet":
        func = name[16:]
        func = func[0:1].lower() + func[1:]
    elif name[0:13] == "virStorageVol":
        func = name[13:]
        func = func[0:1].lower() + func[1:]
    elif name[0:13] == "virNodeDevice":
        if name[13:16] == "Get":
            func = name[16].lower() + name[17:]
        elif name[13:19] == "Lookup" or name[13:19] == "Create":
            func = name[3].lower() + name[4:]
        else:
            func = name[13].lower() + name[14:]
    elif name[0:7] == "virNode":
        func = name[7:]
        func = func[0:1].lower() + func[1:]
    elif name[0:10] == "virConnect":
        func = name[10:]
        func = func[0:1].lower() + func[1:]
    elif name[0:3] == "xml":
        func = name[3:]
        func = func[0:1].lower() + func[1:]
    else:
        func = name
    if func == "iD":
        func = "ID"
    if func == "uUID":
        func = "UUID"
    if func == "uUIDString":
        func = "UUIDString"
    if func == "oSType":
        func = "OSType"
    if func == "xMLDesc":
        func = "XMLDesc"
    if func == "mACString":
        func = "MACString"

    return func


def functionSortKey(info):
    (index, func, name, ret, args, filename, mod) = info
    return func, filename

def writeDoc(module, name, args, indent, output):
     if module == "libvirt":
         funcs = functions
     elif module == "libvirt-lxc":
         funcs = lxc_functions
     elif module == "libvirt-qemu":
         funcs = qemu_functions
     if funcs[name][0] is None or funcs[name][0] == "":
         return
     val = funcs[name][0]
     val = val.replace("NULL", "None")
     output.write(indent)
     output.write('"""')
     i = val.find("\n")
     while i >= 0:
         str = val[0:i+1]
         val = val[i+1:]
         output.write(str)
         i = val.find("\n")
         output.write(indent)
     output.write(val)
     output.write(' """\n')

def buildWrappers(module):
    global ctypes
    global py_types
    global unknown_types
    global functions
    global function_classes
    global classes_type
    global classes_list
    global primary_classes
    global classes_destructors
    global functions_noexcept

    if not module == "libvirt":
        print("ERROR: Unknown module type: %s" % module)
        return None

    for type in list(classes_type.keys()):
        function_classes[classes_type[type][2]] = []

    #
    # Build the list of C types to look for ordered to start
    # with primary classes
    #
    ctypes = []
    classes_list = []
    ctypes_processed = {}
    classes_processed = {}
    for classe in primary_classes:
        classes_list.append(classe)
        classes_processed[classe] = ()
        for type in list(classes_type.keys()):
            tinfo = classes_type[type]
            if tinfo[2] == classe:
                ctypes.append(type)
                ctypes_processed[type] = ()
    for type in list(classes_type.keys()):
        if type in ctypes_processed:
            continue
        tinfo = classes_type[type]
        if tinfo[2] not in classes_processed:
            classes_list.append(tinfo[2])
            classes_processed[tinfo[2]] = ()

        ctypes.append(type)
        ctypes_processed[type] = ()

    for name in list(functions.keys()):
        found = 0
        (desc, ret, args, file, mod, cond) = functions[name]
        for type in ctypes:
            classe = classes_type[type][2]

            if name[0:3] == "vir" and len(args) >= 1 and args[0][1] == type:
                found = 1
                func = nameFixup(name, classe, type, file)
                info = (0, func, name, ret, args, file, mod)
                function_classes[classe].append(info)
                break
            elif name[0:3] == "vir" and len(args) >= 2 and args[1][1] == type \
                and file != "python_accessor" and not name in function_skip_index_one:
                found = 1
                func = nameFixup(name, classe, type, file)
                info = (1, func, name, ret, args, file, mod)
                function_classes[classe].append(info)
                break
        if found == 1:
            continue
        func = nameFixup(name, "None", file, file)
        info = (0, func, name, ret, args, file, mod)
        function_classes['None'].append(info)

    classes_file = "build/%s.py" % module
    extra_file = "%s-override.py" % module
    extra = None

    classes = open(classes_file, "w")

    if os.path.exists(extra_file):
        extra = open(extra_file, "r")
    classes.write("#\n")
    classes.write("# WARNING WARNING WARNING WARNING\n")
    classes.write("#\n")
    classes.write("# This file is automatically written by generator.py. Any changes\n")
    classes.write("# made here will be lost.\n")
    classes.write("#\n")
    classes.write("# To change the manually written methods edit " + module + "-override.py\n")
    classes.write("# To change the automatically written methods edit generator.py\n")
    classes.write("#\n")
    classes.write("# WARNING WARNING WARNING WARNING\n")
    classes.write("#\n")
    if extra is not None:
        classes.writelines(extra.readlines())
    classes.write("#\n")
    classes.write("# WARNING WARNING WARNING WARNING\n")
    classes.write("#\n")
    classes.write("# Automatically written part of python bindings for libvirt\n")
    classes.write("#\n")
    classes.write("# WARNING WARNING WARNING WARNING\n")
    if extra is not None:
        extra.close()

    if "None" in function_classes:
        flist = function_classes["None"]
        flist.sort(key=functionSortKey)
        oldfile = ""
        for info in flist:
            (index, func, name, ret, args, file, mod) = info
            if file != oldfile:
                classes.write("#\n# Functions from module %s\n#\n\n" % file)
                oldfile = file
            classes.write("def %s(" % func)
            n = 0
            for arg in args:
                if n != 0:
                    classes.write(", ")
                classes.write("%s" % arg[0])
                if arg[0] == "flags" or is_optional_arg(arg[2]):
                    if is_integral_type(arg[1]):
                        classes.write("=0")
                    else:
                        classes.write("=None")
                n = n + 1
            classes.write("):\n")
            writeDoc(module, name, args, '    ', classes)

            for arg in args:
                if arg[1] in classes_type:
                    classes.write("    if %s is None: %s__o = None\n" %
                                  (arg[0], arg[0]))
                    classes.write("    else: %s__o = %s%s\n" %
                                  (arg[0], arg[0], classes_type[arg[1]][0]))
            if ret[0] != "void":
                classes.write("    ret = ")
            else:
                classes.write("    ")
            classes.write("libvirtmod.%s(" % name)
            n = 0
            for arg in args:
                if n != 0:
                    classes.write(", ")
                classes.write("%s" % arg[0])
                if arg[1] in classes_type:
                    classes.write("__o")
                n = n + 1
            classes.write(")\n")

            if ret[0] != "void":
                if ret[0] in classes_type:
                    #
                    # Raise an exception
                    #
                    if name in functions_noexcept:
                        classes.write("    if ret is None:return None\n")
                    else:
                        classes.write(
                     "    if ret is None:raise libvirtError('%s() failed')\n" %
                                      (name))

                    classes.write("    return ")
                    classes.write(classes_type[ret[0]][1] % ("ret"))
                    classes.write("\n")

                # For functions returning an integral type there are
                # several things that we can do, depending on the
                # contents of functions_int_*:
                elif is_integral_type (ret[0]):
                    if name not in functions_noexcept:
                        if name in functions_int_exception_test:
                            test = functions_int_exception_test[name]
                        else:
                            test = functions_int_default_test
                        classes.write (("    if " + test +
                                        ": raise libvirtError ('%s() failed')\n") %
                                       ("ret", name))
                    classes.write("    return ret\n")

                elif is_python_noninteger_type (ret[0]):
                    if name not in functions_noexcept:
                        classes.write (("    if %s is None" +
                                        ": raise libvirtError ('%s() failed')\n") %
                                       ("ret", name))
                    classes.write("    return ret\n")

                else:
                    classes.write("    return ret\n")

            classes.write("\n")

    for classname in classes_list:
        if classname == "None":
            pass
        else:
            classes.write("class %s(object):\n" % (classname))
            if classname == "virStorageVol":
                classes.write("    # The size (in bytes) of buffer used in sendAll(),\n")
                classes.write("    # recvAll(), sparseSendAll() and sparseRecvAll()\n")
                classes.write("    # methods. This corresponds to the size of payload\n")
                classes.write("    # of a stream packet.\n")
                classes.write("    streamBufSize = 262120\n\n")
            if classname in [ "virDomain", "virNetwork", "virInterface", "virStoragePool",
                              "virStorageVol", "virNodeDevice", "virSecret","virStream",
                              "virNWFilter", "virNWFilterBinding" ]:
                classes.write("    def __init__(self, conn, _obj=None):\n")
            elif classname in [ "virDomainCheckpoint", "virDomainSnapshot" ]:
                classes.write("    def __init__(self, dom, _obj=None):\n")
            elif classname in [ "virNetworkPort" ]:
                classes.write("    def __init__(self, net, _obj=None):\n")
            else:
                classes.write("    def __init__(self, _obj=None):\n")
            if classname in [ "virDomain", "virNetwork", "virInterface",
                              "virNodeDevice", "virSecret", "virStream",
                              "virNWFilter", "virNWFilterBinding" ]:
                classes.write("        self._conn = conn\n")
            elif classname in [ "virStorageVol", "virStoragePool" ]:
                classes.write("        self._conn = conn\n" + \
                              "        if not isinstance(conn, virConnect):\n" + \
                              "            self._conn = conn._conn\n")
            elif classname in [ "virDomainCheckpoint", "virDomainSnapshot" ]:
                classes.write("        self._dom = dom\n")
                classes.write("        self._conn = dom.connect()\n")
            elif classname in [ "virNetworkPort" ]:
                classes.write("        self._net = net\n")
                classes.write("        self._conn = net.connect()\n")
            classes.write("        if type(_obj).__name__ not in [\"PyCapsule\", \"PyCObject\"]:\n")
            classes.write("            raise Exception(\"Expected a wrapped C Object but got %s\" % type(_obj))\n")
            classes.write("        self._o = _obj\n\n")
            destruct=None
            if classname in classes_destructors:
                classes.write("    def __del__(self):\n")
                classes.write("        if self._o is not None:\n")
                classes.write("            libvirtmod.%s(self._o)\n" %
                              classes_destructors[classname])
                classes.write("        self._o = None\n\n")
                destruct=classes_destructors[classname]

            if classname not in class_skip_connect_impl:
                # Build python safe 'connect' method
                classes.write("    def connect(self):\n")
                classes.write("        return self._conn\n\n")

            if classname in class_domain_impl:
                classes.write("    def domain(self):\n")
                classes.write("        return self._dom\n\n")

            if classname in class_network_impl:
                classes.write("    def network(self):\n")
                classes.write("        return self._net\n\n")

            classes.write("    def c_pointer(self):\n")
            classes.write("        \"\"\"Get C pointer to underlying object\"\"\"\n")
            classes.write("        return libvirtmod.%s_pointer(self._o)\n\n" %
                          classname)

            flist = function_classes[classname]
            flist.sort(key=functionSortKey)
            oldfile = ""
            for info in flist:
                (index, func, name, ret, args, file, mod) = info
                #
                # Do not provide as method the destructors for the class
                # to avoid double free
                #
                if name == destruct:
                    continue
                if file != oldfile:
                    if file == "python_accessor":
                        classes.write("    # accessors for %s\n" % (classname))
                    else:
                        classes.write("    #\n")
                        classes.write("    # %s functions from module %s\n" % (
                                      classname, file))
                        classes.write("    #\n\n")
                oldfile = file
                classes.write("    def %s(self" % func)
                n = 0
                for arg in args:
                    if n != index:
                        classes.write(", %s" % arg[0])
                    if arg[0] == "flags" or is_optional_arg(arg[2]):
                        if is_integral_type(arg[1]):
                           classes.write("=0")
                        else:
                           classes.write("=None")
                    n = n + 1
                classes.write("):\n")
                writeDoc(module, name, args, '        ', classes)
                n = 0
                for arg in args:
                    if arg[1] in classes_type:
                        if n != index:
                            classes.write("        if %s is None: %s__o = None\n" %
                                          (arg[0], arg[0]))
                            classes.write("        else: %s__o = %s%s\n" %
                                          (arg[0], arg[0], classes_type[arg[1]][0]))
                    n = n + 1
                if ret[0] != "void":
                    classes.write("        ret = ")
                else:
                    classes.write("        ")
                n = 0
                classes.write("libvirtmod.%s(" % name)
                for arg in args:
                    if n != 0:
                        classes.write(", ")
                    if n != index:
                        classes.write("%s" % arg[0])
                        if arg[1] in classes_type:
                            classes.write("__o")
                    else:
                        classes.write("self")
                        if arg[1] in classes_type:
                            classes.write(classes_type[arg[1]][0])
                    n = n + 1
                classes.write(")\n")

                if name == "virConnectClose":
                    classes.write("        self._o = None\n")

                # For functions returning object types:
                if ret[0] != "void":
                    if ret[0] in classes_type:
                        #
                        # Raise an exception
                        #
                        if name in functions_noexcept:
                            classes.write(
                                "        if ret is None:return None\n")
                        else:
                            if classname == "virConnect":
                                classes.write(
                     "        if ret is None:raise libvirtError('%s() failed', conn=self)\n" %
                                              (name))
                            elif classname == "virDomain":
                                classes.write(
                     "        if ret is None:raise libvirtError('%s() failed', dom=self)\n" %
                                              (name))
                            elif classname == "virNetwork":
                                classes.write(
                     "        if ret is None:raise libvirtError('%s() failed', net=self)\n" %
                                              (name))
                            elif classname == "virInterface":
                                classes.write(
                     "        if ret is None:raise libvirtError('%s() failed', net=self)\n" %
                                              (name))
                            elif classname == "virStoragePool":
                                classes.write(
                     "        if ret is None:raise libvirtError('%s() failed', pool=self)\n" %
                                              (name))
                            elif classname == "virStorageVol":
                                classes.write(
                     "        if ret is None:raise libvirtError('%s() failed', vol=self)\n" %
                                              (name))
                            elif classname in [ "virDomainCheckpoint", "virDomainSnapshot"]:
                                classes.write(
                     "        if ret is None:raise libvirtError('%s() failed', dom=self._dom)\n" %
                                              (name))
                            else:
                                classes.write(
                     "        if ret is None:raise libvirtError('%s() failed')\n" %
                                              (name))

                        #
                        # generate the returned class wrapper for the object
                        #
                        classes.write("        __tmp = ")
                        classes.write(classes_type[ret[0]][1] % ("ret"))
                        classes.write("\n")

                        #
                        # return the class
                        #
                        classes.write("        return __tmp\n")

                    # For functions returning an integral type there
                    # are several things that we can do, depending on
                    # the contents of functions_int_*:
                    elif is_integral_type (ret[0]):
                        if name not in functions_noexcept:
                            if name in functions_int_exception_test:
                                test = functions_int_exception_test[name]
                            else:
                                test = functions_int_default_test
                            if classname == "virConnect":
                                classes.write (("        if " + test +
                                                ": raise libvirtError ('%s() failed', conn=self)\n") %
                                               ("ret", name))
                            elif classname == "virDomain":
                                classes.write (("        if " + test +
                                                ": raise libvirtError ('%s() failed', dom=self)\n") %
                                               ("ret", name))
                            elif classname == "virNetwork":
                                classes.write (("        if " + test +
                                                ": raise libvirtError ('%s() failed', net=self)\n") %
                                               ("ret", name))
                            elif classname == "virInterface":
                                classes.write (("        if " + test +
                                                ": raise libvirtError ('%s() failed', net=self)\n") %
                                               ("ret", name))
                            elif classname == "virStoragePool":
                                classes.write (("        if " + test +
                                                ": raise libvirtError ('%s() failed', pool=self)\n") %
                                               ("ret", name))
                            elif classname == "virStorageVol":
                                classes.write (("        if " + test +
                                                ": raise libvirtError ('%s() failed', vol=self)\n") %
                                               ("ret", name))
                            else:
                                classes.write (("        if " + test +
                                                ": raise libvirtError ('%s() failed')\n") %
                                               ("ret", name))

                        classes.write ("        return ret\n")

                    elif is_python_noninteger_type (ret[0]):
                        if name not in functions_noexcept:
                            if classname == "virConnect":
                                classes.write (("        if %s is None" +
                                                ": raise libvirtError ('%s() failed', conn=self)\n") %
                                               ("ret", name))
                            elif classname == "virDomain":
                                classes.write (("        if %s is None" +
                                                ": raise libvirtError ('%s() failed', dom=self)\n") %
                                               ("ret", name))
                            elif classname == "virNetwork":
                                classes.write (("        if %s is None" +
                                                ": raise libvirtError ('%s() failed', net=self)\n") %
                                               ("ret", name))
                            elif classname == "virInterface":
                                classes.write (("        if %s is None" +
                                                ": raise libvirtError ('%s() failed', net=self)\n") %
                                               ("ret", name))
                            elif classname == "virStoragePool":
                                classes.write (("        if %s is None" +
                                                ": raise libvirtError ('%s() failed', pool=self)\n") %
                                               ("ret", name))
                            elif classname == "virStorageVol":
                                classes.write (("        if %s is None" +
                                                ": raise libvirtError ('%s() failed', vol=self)\n") %
                                               ("ret", name))
                            else:
                                classes.write (("        if %s is None" +
                                                ": raise libvirtError ('%s() failed')\n") %
                                               ("ret", name))

                        classes.write ("        return ret\n")
                    else:
                        classes.write("        return ret\n")

                classes.write("\n")
            # Append "<classname>.py" to class def, iff it exists
            try:
                wantfuncs = []
                extra = open("libvirt-override-" + classname + ".py", "r")
                classes.write ("    #\n")
                classes.write ("    # %s methods from %s.py (hand coded)\n" % (classname,classname))
                classes.write ("    #\n")
                cached = None


                # Since we compile with older libvirt, we don't want to pull
                # in manually written python methods which call C methods
                # that don't exist. This code attempts to detect which
                # methods to skip by looking at the libvirtmod.XXXX calls

                def shouldSkip(lines):
                    for line in lines:
                        offset = line.find("libvirtmod.")
                        if offset != -1:
                            func = line[offset + 11:]
                            offset = func.find("(")
                            func = func[0:offset]
                            if func not in functions_skipped:
                                return True
                    return False

                for line in extra.readlines():
                    offset = line.find(" def ")
                    if offset != -1:
                        name = line[offset+5:]
                        offset = name.find("(")
                        name = name[0:offset]
                        if cached is not None:
                            if not shouldSkip(cached):
                                classes.writelines(cached)
                        if name == "__del__":
                            cached = None
                            classes.write(line)
                        else:
                            cached = [line]
                    else:
                        if cached is not None:
                            cached.append(line)
                        else:
                            classes.write(line)
                if not shouldSkip(cached):
                    classes.writelines(cached)
                classes.write("\n")
                extra.close()
            except:
                pass

    #
    # Generate enum constants
    #
    def enumsSortKey(data):
        value = data[1]
        try:
            value = int(value)
        except ValueError:
            value = float('inf')
        return value, data[0]

    # Resolve only one level of reference
    def resolveEnum(enum, data):
        for name,val in enum.items():
            try:
                int(val)
            except ValueError:
                enum[name] = data[val]
        return enum

    enumvals = list(enums.items())
    # convert list of dicts to one dict
    enumData = {}
    for type,enum in enumvals:
        enumData.update(enum)

    if enumvals is not None:
        enumvals.sort(key=lambda x: x[0])
    for type,enum in enumvals:
        classes.write("# %s\n" % type)
        items = list(resolveEnum(enum, enumData).items())
        items.sort(key=enumsSortKey)
        if items[-1][0].endswith('_LAST'):
            del items[-1]
        for name,value in items:
            classes.write("%s = %s\n" % (name,value))
        classes.write("\n")

    classes.write("# typed parameter names\n")
    for name, value in params:
        classes.write("%s = \"%s\"\n" % (name, value))

    classes.close()

def qemuBuildWrappers(module):
    global qemu_functions

    if not module == "libvirt-qemu":
        print("ERROR: only libvirt-qemu is supported")
        return None

    extra_file = "%s-override.py" % module
    extra = None

    fd = open("build/libvirt_qemu.py", "w")

    if os.path.exists(extra_file):
        extra = open(extra_file, "r")
    fd.write("#\n")
    fd.write("# WARNING WARNING WARNING WARNING\n")
    fd.write("#\n")
    fd.write("# This file is automatically written by generator.py. Any changes\n")
    fd.write("# made here will be lost.\n")
    fd.write("#\n")
    fd.write("# To change the manually written methods edit " + module + "-override.py\n")
    fd.write("# To change the automatically written methods edit generator.py\n")
    fd.write("#\n")
    fd.write("# WARNING WARNING WARNING WARNING\n")
    fd.write("#\n")
    fd.write("# Automatically written part of python bindings for libvirt\n")
    fd.write("#\n")

    fd.write("import sys\n")

    fd.write("try:\n")
    fd.write("    import libvirtmod_qemu\n")
    fd.write("except ImportError:\n")
    fd.write("    lib_e = sys.exc_info()[1]\n")
    fd.write("    try:\n")
    fd.write("        import cygvirtmod_qemu as libvirtmod_qemu\n")
    fd.write("    except ImportError:\n")
    fd.write("        cyg_e = sys.exc_info()[1]\n")
    fd.write("        if str(cyg_e).count(\"No module named\"):\n")
    fd.write("            raise lib_e\n\n")

    fd.write("import libvirt\n\n")
    fd.write("# WARNING WARNING WARNING WARNING\n")
    fd.write("#\n")
    if extra is not None:
        fd.writelines(extra.readlines())
    fd.write("#\n")
    if extra is not None:
        extra.close()

    fd.write("# WARNING WARNING WARNING WARNING\n")
    fd.write("#\n")
    fd.write("#\n# Functions from module %s\n#\n\n" % module)
    #
    # Generate functions directly, no classes
    #
    for name in sorted(qemu_functions.keys()):
        func = nameFixup(name, 'None', None, None)
        (desc, ret, args, file, mod, cond) = qemu_functions[name]
        fd.write("def %s(" % func)
        n = 0
        for arg in args:
            if n != 0:
                fd.write(", ")
            fd.write("%s" % arg[0])
            n = n + 1
        fd.write("):\n")
        writeDoc(module, name, args, '    ', fd)

        if ret[0] != "void":
            fd.write("    ret = ")
        else:
            fd.write("    ")
        fd.write("libvirtmod_qemu.%s(" % name)
        n = 0

        conn = None

        for arg in args:
            if arg[1] == "virConnectPtr":
                conn = arg[0]

            if n != 0:
                fd.write(", ")
            if arg[1] in ["virDomainPtr", "virConnectPtr"]:
                # FIXME: This might have problem if the function
                # has multiple args which are objects.
                fd.write("%s.%s" % (arg[0], "_o"))
            else:
                fd.write("%s" % arg[0])
            n = n + 1
        fd.write(")\n")

        if ret[0] != "void":
            fd.write("    if ret is None: raise libvirt.libvirtError('" + name + "() failed')\n")
            if ret[0] == "virDomainPtr":
                fd.write("    __tmp = libvirt.virDomain(" + conn + ", _obj=ret)\n")
                fd.write("    return __tmp\n")
            else:
                fd.write("    return ret\n")

        fd.write("\n")

    #
    # Generate enum constants
    #
    for type,enum in sorted(qemu_enums.items()):
        fd.write("# %s\n" % type)
        items = list(enum.items())
        items.sort(key=lambda i: (int(i[1]), i[0]))
        for name,value in items:
            fd.write("%s = %s\n" % (name,value))
        fd.write("\n")

    fd.close()


def lxcBuildWrappers(module):
    global lxc_functions

    if not module == "libvirt-lxc":
        print("ERROR: only libvirt-lxc is supported")
        return None

    extra_file = "%s-override.py" % module
    extra = None

    fd = open("build/libvirt_lxc.py", "w")

    if os.path.exists(extra_file):
        extra = open(extra_file, "r")
    fd.write("#\n")
    fd.write("# WARNING WARNING WARNING WARNING\n")
    fd.write("#\n")
    fd.write("# This file is automatically written by generator.py. Any changes\n")
    fd.write("# made here will be lost.\n")
    fd.write("#\n")
    fd.write("# To change the manually written methods edit " + module + "-override.py\n")
    fd.write("# To change the automatically written methods edit generator.py\n")
    fd.write("#\n")
    fd.write("# WARNING WARNING WARNING WARNING\n")
    fd.write("#\n")
    if extra is not None:
        fd.writelines(extra.readlines())
    fd.write("#\n")
    fd.write("# WARNING WARNING WARNING WARNING\n")
    fd.write("#\n")
    fd.write("# Automatically written part of python bindings for libvirt\n")
    fd.write("#\n")
    fd.write("# WARNING WARNING WARNING WARNING\n")
    if extra is not None:
        extra.close()

    fd.write("import sys\n")

    fd.write("try:\n")
    fd.write("    import libvirtmod_lxc\n")
    fd.write("except ImportError:\n")
    fd.write("    lib_e = sys.exc_info()[1]\n")
    fd.write("    try:\n")
    fd.write("        import cygvirtmod_lxc as libvirtmod_lxc\n")
    fd.write("    except ImportError:\n")
    fd.write("        cyg_e = sys.exc_info()[1]\n")
    fd.write("        if str(cyg_e).count(\"No module named\"):\n")
    fd.write("            raise lib_e\n\n")

    fd.write("import libvirt\n\n")
    fd.write("#\n# Functions from module %s\n#\n\n" % module)
    #
    # Generate functions directly, no classes
    #
    for name in sorted(lxc_functions.keys()):
        func = nameFixup(name, 'None', None, None)
        (desc, ret, args, file, mod, cond) = lxc_functions[name]
        fd.write("def %s(" % func)
        n = 0
        for arg in args:
            if n != 0:
                fd.write(", ")
            fd.write("%s" % arg[0])
            n = n + 1
        fd.write("):\n")
        writeDoc(module, name, args, '    ', fd)

        if ret[0] != "void":
            fd.write("    ret = ")
        else:
            fd.write("    ")
        fd.write("libvirtmod_lxc.%s(" % name)
        n = 0

        conn = None

        for arg in args:
            if arg[1] == "virConnectPtr":
                conn = arg[0]

            if n != 0:
                fd.write(", ")
            if arg[1] in ["virDomainPtr", "virConnectPtr"]:
                # FIXME: This might have problem if the function
                # has multiple args which are objects.
                fd.write("%s.%s" % (arg[0], "_o"))
            else:
                fd.write("%s" % arg[0])
            n = n + 1
        fd.write(")\n")

        if ret[0] != "void":
            fd.write("    if ret is None: raise libvirt.libvirtError('" + name + "() failed')\n")
            if ret[0] == "virDomainPtr":
                fd.write("    __tmp = libvirt.virDomain(" + conn + ", _obj=ret)\n")
                fd.write("    return __tmp\n")
            else:
                fd.write("    return ret\n")

        fd.write("\n")

    #
    # Generate enum constants
    #
    for type,enum in sorted(lxc_enums.items()):
        fd.write("# %s\n" % type)
        items = list(enum.items())
        items.sort(key=lambda i: (int(i[1]), i[0]))
        for name,value in items:
            fd.write("%s = %s\n" % (name,value))
        fd.write("\n")

    fd.close()


quiet = 0
if not os.path.exists("build"):
    os.mkdir("build")

if buildStubs(sys.argv[1], sys.argv[2]) < 0:
    sys.exit(1)

if sys.argv[1] == "libvirt":
    buildWrappers(sys.argv[1])
elif sys.argv[1] == "libvirt-lxc":
    lxcBuildWrappers(sys.argv[1])
elif sys.argv[1] == "libvirt-qemu":
    qemuBuildWrappers(sys.argv[1])
else:
    print("ERROR: unknown module %s" % sys.argv[1])
    sys.exit(1)

sys.exit(0)
