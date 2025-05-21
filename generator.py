#!/usr/bin/env python3
#
# generate python wrappers from the XML API description
#

import os
import re
import sys
import xml.sax
from contextlib import closing
from collections import defaultdict
from typing import Dict, IO, List, Optional, Set, Tuple, Union  # noqa F401
ArgumentType = Tuple[str, str, str]
FunctionType = Tuple[str, ArgumentType, List[ArgumentType], str, str, str]
EnumValue = Union[str, int]
EnumType = Dict[str, EnumValue]

functions = {}  # type: Dict[str, FunctionType]
enums = defaultdict(dict)  # type: Dict[str, EnumType] # { enumType: { enumConstant: enumValue } }
event_ids = []  # type: List[str]
params = []  # type: List[Tuple[str, str]] # [ (paramName, paramValue)... ]


quiet = True

#######################################################################
#
#  That part if purely the API acquisition phase from the
#  libvirt API description
#
#######################################################################
debug = 0
onlyOverrides = False
sourceDir = "."
buildDir = "build"

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

def openSourceFile(file: str, mode: str = "r", optional: bool = False):
    path = os.path.join(sourceDir, file)
    if optional and not os.path.exists(path):
        return None
    return open(path, mode)

def parse(data: IO[str]) -> None:
    target = docParser()
    with closing(xml.sax.make_parser()) as parser:
        parser.setContentHandler(target)
        parser.parse(data)


class docParser(xml.sax.handler.ContentHandler):
    def __init__(self) -> None:
        self._data = []  # type: List[str]
        self.in_function = False

    def characters(self, text: str) -> None:
        if debug:
            print("data %s" % text)
        self._data.append(text)

    def startElement(self, tag: str, attrs: Dict[str, str]) -> None:
        if debug:
            print("start %s, %s" % (tag, attrs))
        if tag == 'function':
            self._data = []
            self.in_function = True
            self.function_cond = ''
            self.function_args = []  # type: List[ArgumentType]
            self.function_descr = ''
            self.function_return = None  # type: Optional[ArgumentType]
            self.function = attrs.get('name', '')
            self.function_file = attrs.get('file', '')
            self.function_module = attrs.get('module', '')
        elif tag == 'cond':
            self._data = []
        elif tag == 'info':
            self._data = []
        elif tag == 'arg':
            if self.in_function:
                self.function_arg_name = attrs.get('name', '')
                if self.function_arg_name == 'from':
                    self.function_arg_name = 'frm'
                self.function_arg_type = attrs.get('type', '')
                self.function_arg_info = attrs.get('info', '')
        elif tag == 'return':
            if self.in_function:
                self.function_return_type = attrs.get('type', '')
                self.function_return_info = attrs.get('info', '')
                self.function_return_field = attrs.get('field', '')
        elif tag == 'enum':
            # enums come from header files, hence virterror.h
            files = libvirt_headers + ["virerror",
                                       "virterror",
                                       "libvirt-lxc",
                                       "libvirt-qemu"]
            if attrs['file'] in files:
                enum(attrs['type'], attrs['name'], attrs['value'])
        elif tag == "macro":
            if "string" in attrs:
                params.append((attrs['name'], attrs['string']))

    def endElement(self, tag: str) -> None:
        if debug:
            print("end %s" % tag)
        if tag == 'function':
            # functions come from source files, hence 'virerror.c'
            if self.function:
                assert self.function_return

                modules = libvirt_headers + ["event",
                                             "virevent",
                                             "virerror",
                                             "virterror",
                                             "libvirt-lxc",
                                             "libvirt-qemu"]
                files = ["python", "python-lxc", "python-qemu"]

                if (self.function_module in modules or
                    self.function_file in files):
                    function(self.function, self.function_descr,
                             self.function_return, self.function_args,
                             self.function_file, self.function_module,
                             self.function_cond)
                self.in_function = False
        elif tag == 'arg':
            if self.in_function:
                self.function_args.append((self.function_arg_name,
                                           self.function_arg_type,
                                           self.function_arg_info))
        elif tag == 'return':
            if self.in_function:
                self.function_return = (self.function_return_type,
                                        self.function_return_info,
                                        self.function_return_field)
        elif tag == 'info':
            str = ''.join(self._data)
            if self.in_function:
                self.function_descr = str
        elif tag == 'cond':
            str = ''.join(self._data)
            if self.in_function:
                self.function_cond = str


def function(name: str, desc: str, ret: ArgumentType, args: List[ArgumentType], file: str, module: str, cond: str) -> None:
    if onlyOverrides and name not in functions:
        return
    if name == "virConnectListDomains":
        name = "virConnectListDomainsID"
    functions[name] = (desc, ret, args, file, module, cond)


def enum(type: str, name: str, value: EnumValue) -> None:
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
    elif value == 'VIR_DOMAIN_AGENT_RESPONSE_TIMEOUT_BLOCK':
        value = -2
    elif value == 'VIR_DOMAIN_AGENT_RESPONSE_TIMEOUT_DEFAULT':
        value = -1
    elif value == 'VIR_DOMAIN_AGENT_RESPONSE_TIMEOUT_NOWAIT':
        value = 0

    if onlyOverrides and name not in enums[type]:
        return
    enums[type][name] = value


#######################################################################
#
#  Some filtering rules to drop functions/types which should not
#  be exposed as-is on the Python interface
#
#######################################################################

skipped_types = {
    # 'int *': "usually a return type",
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
    'void': ('', '', '', ''),
    'int': ('i', '', "int", "int"),
    'long': ('l', '', "long", "long"),
    'double': ('d', '', "double", "double"),
    'unsigned int': ('I', '', "int", "int"),
    'unsigned long': ('l', '', "long", "long"),
    'long long': ('L', '', "longlong", "long long"),
    'unsigned long long': ('L', '', "longlong", "long long"),
    'unsigned char *': ('z', '', "charPtr", "char *"),
    'char *': ('z', '', "charPtr", "char *"),
    'const char *': ('z', '', "constcharPtr", "const char *"),
    'size_t': ('n', '', "size_t", "size_t"),

    'virDomainPtr': ('O', "virDomain", "virDomainPtr", "virDomainPtr"),
    'virDomain *': ('O', "virDomain", "virDomainPtr", "virDomainPtr"),
    'const virDomain *': ('O', "virDomain", "virDomainPtr", "virDomainPtr"),

    'virNetworkPtr': ('O', "virNetwork", "virNetworkPtr", "virNetworkPtr"),
    'virNetwork *': ('O', "virNetwork", "virNetworkPtr", "virNetworkPtr"),
    'const virNetwork *': ('O', "virNetwork", "virNetworkPtr", "virNetworkPtr"),

    'virNetworkPortPtr': ('O', "virNetworkPort", "virNetworkPortPtr", "virNetworkPortPtr"),
    'virNetworkPort *': ('O', "virNetworkPort", "virNetworkPortPtr", "virNetworkPortPtr"),
    'const virNetworkPort *': ('O', "virNetworkPort", "virNetworkPortPtr", "virNetworkPortPtr"),

    'virInterfacePtr': ('O', "virInterface", "virInterfacePtr", "virInterfacePtr"),
    'virInterface *': ('O', "virInterface", "virInterfacePtr", "virInterfacePtr"),
    'const virInterface *': ('O', "virInterface", "virInterfacePtr", "virInterfacePtr"),

    'virStoragePoolPtr': ('O', "virStoragePool", "virStoragePoolPtr", "virStoragePoolPtr"),
    'virStoragePool *': ('O', "virStoragePool", "virStoragePoolPtr", "virStoragePoolPtr"),
    'const virStoragePool *': ('O', "virStoragePool", "virStoragePoolPtr", "virStoragePoolPtr"),

    'virStorageVolPtr': ('O', "virStorageVol", "virStorageVolPtr", "virStorageVolPtr"),
    'virStorageVol *': ('O', "virStorageVol", "virStorageVolPtr", "virStorageVolPtr"),
    'const virStorageVol *': ('O', "virStorageVol", "virStorageVolPtr", "virStorageVolPtr"),

    'virConnectPtr': ('O', "virConnect", "virConnectPtr", "virConnectPtr"),
    'virConnect *': ('O', "virConnect", "virConnectPtr", "virConnectPtr"),
    'const virConnect *': ('O', "virConnect", "virConnectPtr", "virConnectPtr"),

    'virNodeDevicePtr': ('O', "virNodeDevice", "virNodeDevicePtr", "virNodeDevicePtr"),
    'virNodeDevice *': ('O', "virNodeDevice", "virNodeDevicePtr", "virNodeDevicePtr"),
    'const virNodeDevice *': ('O', "virNodeDevice", "virNodeDevicePtr", "virNodeDevicePtr"),

    'virSecretPtr': ('O', "virSecret", "virSecretPtr", "virSecretPtr"),
    'virSecret *': ('O', "virSecret", "virSecretPtr", "virSecretPtr"),
    'const virSecret *': ('O', "virSecret", "virSecretPtr", "virSecretPtr"),

    'virNWFilterPtr': ('O', "virNWFilter", "virNWFilterPtr", "virNWFilterPtr"),
    'virNWFilter *': ('O', "virNWFilter", "virNWFilterPtr", "virNWFilterPtr"),
    'const virNWFilter *': ('O', "virNWFilter", "virNWFilterPtr", "virNWFilterPtr"),

    'virNWFilterBindingPtr': ('O', "virNWFilterBinding", "virNWFilterBindingPtr", "virNWFilterBindingPtr"),
    'virNWFilterBinding *': ('O', "virNWFilterBinding", "virNWFilterBindingPtr", "virNWFilterBindingPtr"),
    'const virNWFilterBinding *': ('O', "virNWFilterBinding", "virNWFilterBindingPtr", "virNWFilterBindingPtr"),

    'virStreamPtr': ('O', "virStream", "virStreamPtr", "virStreamPtr"),
    'virStream *': ('O', "virStream", "virStreamPtr", "virStreamPtr"),
    'const virStream *': ('O', "virStream", "virStreamPtr", "virStreamPtr"),

    'virDomainCheckpointPtr': ('O', "virDomainCheckpoint", "virDomainCheckpointPtr", "virDomainCheckpointPtr"),
    'virDomainCheckpoint *': ('O', "virDomainCheckpoint", "virDomainCheckpointPtr", "virDomainCheckpointPtr"),
    'const virDomainCheckpoint *': ('O', "virDomainCheckpoint", "virDomainCheckpointPtr", "virDomainCheckpointPtr"),

    'virDomainSnapshotPtr': ('O', "virDomainSnapshot", "virDomainSnapshotPtr", "virDomainSnapshotPtr"),
    'virDomainSnapshot *': ('O', "virDomainSnapshot", "virDomainSnapshotPtr", "virDomainSnapshotPtr"),
    'const virDomainSnapshot *': ('O', "virDomainSnapshot", "virDomainSnapshotPtr", "virDomainSnapshotPtr"),
}  # type: Dict[str, Tuple[str, str, str, str]]


#######################################################################
#
#  This part writes the C <-> Python stubs libvirt.[ch] and
#  the table libvirt-export.c.inc to add when registering the Python module
#
#######################################################################

# Class methods which are written by hand in libvirt.c but the Python-level
# code is still automatically generated (so they are not in skip_function()).
skip_impl = {
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
    'virDomainSetLaunchSecurityState',
    'virNodeGetSEVInfo',
    'virNetworkPortGetParameters',
    'virNetworkPortSetParameters',
    'virDomainGetGuestInfo',
    'virDomainAuthorizedSSHKeysGet',
    'virDomainAuthorizedSSHKeysSet',
    'virDomainGetMessages',
    'virNodeDeviceGetAutostart',
    'virDomainSaveParams',
    'virDomainRestoreParams',
    'virDomainGetAutostartOnce',
    'virDomainSetThrottleGroup',

    'virDomainLxcOpenNamespace',

    'virDomainQemuMonitorCommand',
    'virDomainQemuAgentCommand',
}


# These are functions which the generator skips completely - no python
# or C code is generated. Generally should not be used for any more
# functions than those already listed
skip_function = {
    'virConnectListDomains',  # Python API is called virConnectListDomainsID for unknown reasons
    'virConnSetErrorFunc',  # Not used in Python API  XXX is this a bug ?
    'virResetError',  # Not used in Python API  XXX is this a bug ?
    'virGetVersion',  # Python C code is manually written
    'virSetErrorFunc',  # Python API is called virRegisterErrorHandler for unknown reasons
    'virConnCopyLastError',  # Python API is called virConnGetLastError instead
    'virCopyLastError',  # Python API is called virGetLastError instead
    'virConnectOpenAuth',  # Python C code is manually written
    'virDefaultErrorFunc',  # Python virErrorFuncHandler impl calls this from C
    'virConnectDomainEventRegister',   # overridden in virConnect.py
    'virConnectDomainEventDeregister',  # overridden in virConnect.py
    'virConnectDomainEventRegisterAny',   # overridden in virConnect.py
    'virConnectDomainEventDeregisterAny',  # overridden in virConnect.py
    'virConnectNetworkEventRegisterAny',   # overridden in virConnect.py
    'virConnectNetworkEventDeregisterAny',  # overridden in virConnect.py
    'virConnectStoragePoolEventRegisterAny',   # overridden in virConnect.py
    'virConnectStoragePoolEventDeregisterAny',  # overridden in virConnect.py
    'virConnectNodeDeviceEventRegisterAny',   # overridden in virConnect.py
    'virConnectNodeDeviceEventDeregisterAny',  # overridden in virConnect.py
    'virConnectSecretEventRegisterAny',   # overridden in virConnect.py
    'virConnectSecretEventDeregisterAny',  # overridden in virConnect.py
    'virSaveLastError',  # We have our own python error wrapper
    'virFreeError',  # Only needed if we use virSaveLastError
    'virConnectListAllDomains',  # overridden in virConnect.py
    'virDomainListAllCheckpoints',  # overridden in virDomain.py
    'virDomainCheckpointListAllChildren',  # overridden in virDomainCheckpoint.py
    'virDomainListAllSnapshots',  # overridden in virDomain.py
    'virDomainSnapshotListAllChildren',  # overridden in virDomainSnapshot.py
    'virConnectListAllStoragePools',  # overridden in virConnect.py
    'virStoragePoolListAllVolumes',  # overridden in virStoragePool.py
    'virConnectListAllNetworks',  # overridden in virConnect.py
    'virNetworkListAllPorts',  # overridden in virConnect.py
    'virConnectListAllInterfaces',  # overridden in virConnect.py
    'virConnectListAllNodeDevices',  # overridden in virConnect.py
    'virConnectListAllNWFilters',  # overridden in virConnect.py
    'virConnectListAllNWFilterBindings',  # overridden in virConnect.py
    'virConnectListAllSecrets',  # overridden in virConnect.py
    'virConnectGetAllDomainStats',  # overridden in virConnect.py
    'virDomainListGetStats',  # overridden in virConnect.py
    'virDomainFDAssociate',  # overridden in virDomain.py

    'virStreamRecvAll',  # Pure python libvirt-override-virStream.py
    'virStreamSendAll',  # Pure python libvirt-override-virStream.py
    'virStreamRecv',  # overridden in libvirt-override-virStream.py
    'virStreamSend',  # overridden in libvirt-override-virStream.py
    'virStreamRecvHole',  # overridden in libvirt-override-virStream.py
    'virStreamSendHole',  # overridden in libvirt-override-virStream.py
    'virStreamRecvFlags',  # overridden in libvirt-override-virStream.py
    'virStreamSparseRecvAll',  # overridden in libvirt-override-virStream.py
    'virStreamSparseSendAll',  # overridden in libvirt-override-virStream.py

    'virConnectUnregisterCloseCallback',  # overridden in virConnect.py
    'virConnectRegisterCloseCallback',  # overridden in virConnect.py

    'virDomainCreateXMLWithFiles',  # overridden in virConnect.py
    'virDomainCreateWithFiles',  # overridden in virDomain.py

    'virDomainFSFreeze',  # overridden in virDomain.py
    'virDomainFSThaw',  # overridden in virDomain.py
    'virDomainGetTime',  # overridden in virDomain.py
    'virDomainSetTime',  # overridden in virDomain.py

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

    'virNetworkDHCPLeaseFree',  # only useful in C, python code uses list
    'virDomainStatsRecordListFree',  # only useful in C, python uses dict
    'virDomainFSInfoFree',  # only useful in C, python code uses list
    'virDomainIOThreadInfoFree',  # only useful in C, python code uses list
    'virDomainInterfaceFree',  # only useful in C, python code uses list

    "virDomainLxcEnterNamespace",
    "virDomainLxcEnterSecurityLabel",

    # "virDomainQemuAttach",
    'virConnectDomainQemuMonitorEventRegister',  # overridden in -qemu.py
    'virConnectDomainQemuMonitorEventDeregister',  # overridden in -qemu.py
    'virDomainQemuMonitorCommandWithFiles', # overridden in -qemu.py
}

# Generate C code, but skip python impl
function_skip_python_impl = {
    "virStreamFree",  # Needed in custom virStream __del__, but free shouldn't
                      # be exposed in bindings
}

function_skip_index_one = {
    "virDomainRevertToSnapshot",
}


def validate_function(name):
    (desc, ret, args, file, mod, cond) = functions[name]

    if name in skip_function:
        return []
    if name in skip_impl:
        return []

    failed = False
    unknown = []
    for a_name, a_type, a_info in args:
        # This should be correct
        if a_type[0:6] == "const ":
            a_type = a_type[6:]

        if a_type in skipped_types:
            return []

        if a_type not in py_types:
            unknown.append(a_type)

    r_type, r_info, r_field = ret
    if r_type in skipped_types:
        return []
    if r_type != 'void' and r_type not in py_types:
        unknown.append(r_type)

    return unknown


def validate_functions():
    unknown_types = defaultdict(list)  # type: Dict[str, List[str]]
    funcs_failed = []  # type: List[str]

    for name in sorted(functions):
        unknown = validate_function(name)
        if unknown:
            funcs_failed.append(name)
            for thetype in unknown:
                unknown_types[thetype].append(name)

    if unknown_types:
        print("Missing type converters: ")
        for type, count in unknown_types.items():
            print("%s:%d " % (type, len(count)))

    for f in funcs_failed:
        print("ERROR: failed %s" % f)

    if funcs_failed:
        return -1

    return 0


def skip_both_impl(name: str) -> bool:
    if name in skip_function:
        return True

    (desc, ret, args, file, mod, cond) = functions[name]

    for a_name, a_type, a_info in args:
        # This should be correct
        if a_type[0:6] == "const ":
            a_type = a_type[6:]

        if a_type in skipped_types:
            return True

    r_type, r_info, r_field = ret
    if r_type in skipped_types:
        return True

    return False


def skip_c_impl(name: str) -> bool:
    if skip_both_impl(name):
        return True

    if name in skip_impl:
        return True

    return False


def skip_py_impl(name: str) -> bool:
    if skip_both_impl(name):
        return True

    if name in function_skip_python_impl:
        return True

    return False


def print_function_wrapper(package: str, name: str, output: IO[str], export: IO[str], include: IO[str]) -> bool:
    """
    :returns: True if generated, False if skipped
    """
    (desc, ret, args, file, mod, cond) = functions[name]

    if skip_c_impl(name):
        return False

    c_call = ""
    format = ""
    format_args = ""
    c_args = ""
    c_return = ""
    c_convert = ""
    num_bufs = 0
    for a_name, a_type, a_info in args:
        # This should be correct
        if a_type[0:6] == "const ":
            a_type = a_type[6:]
        c_args += "    %s %s;\n" % (a_type, a_name)
        if a_type in py_types:
            (f, t, n, c) = py_types[a_type]
            if f:
                format += f
            if t:
                format_args += ", &pyobj_%s" % (a_name)
                c_args += "    PyObject *pyobj_%s;\n" % (a_name)
                c_convert += \
                    "    %s = (%s) Py%s_Get(pyobj_%s);\n" % (
                        a_name, a_type, t, a_name)
            else:
                format_args += ", &%s" % (a_name)
            if f == 't#':
                format_args += ", &py_buffsize%d" % num_bufs
                c_args += "    int py_buffsize%d;\n" % num_bufs
                num_bufs += 1
            if c_call:
                c_call += ", "
            c_call += "%s" % (a_name)
        else:
            raise Exception("Unexpected type %s in function %s" % (a_type, name))
    if format:
        format += ":%s" % (name)

    r_type, r_info, r_field = ret
    if r_type == 'void':
        if file == "python_accessor":
            if args[1][1] == "char *":
                c_call = "\n    VIR_FREE(%s->%s);\n" % (
                    args[0][0], args[1][0])
                c_call += "    %s->%s = (%s)strdup((const xmlChar *)%s);\n" % (
                    args[0][0], args[1][0], args[1][1], args[1][0])
            else:
                c_call = "\n    %s->%s = %s;\n" % (args[0][0], args[1][0],
                                                   args[1][0])
        else:
            c_call = "\n    %s(%s);\n" % (name, c_call)
        ret_convert = "    Py_INCREF(Py_None);\n    return Py_None;\n"
    elif r_type in py_types:
        (f, t, n, c) = py_types[r_type]
        c_return = "    %s c_retval;\n" % (r_type)
        if file == "python_accessor" and r_field:
            c_call = "\n    c_retval = %s->%s;\n" % (args[0][0], r_field)
        else:
            c_call = "\n    c_retval = %s(%s);\n" % (name, c_call)
        ret_convert = "    py_retval = libvirt_%sWrap((%s) c_retval);\n" % (n, c)
        if n == "charPtr":
            ret_convert += "    free(c_retval);\n"
        ret_convert += "    return py_retval;\n"
    else:
        raise Exception("Unexpected type %s in function %s" % (r_type, name))

    if cond:
        include.write("#if %s\n" % cond)
        export.write("#if %s\n" % cond)
        output.write("#if %s\n" % cond)

    include.write("PyObject * ")
    include.write("%s_%s(PyObject *self, PyObject *args);\n" % (package, name))
    export.write("    { (char *)\"%s\", %s_%s, METH_VARARGS, NULL },\n" %
                 (name, package, name))

    if file == "python":
        # Those have been manually generated
        if cond:
            include.write("#endif\n")
            export.write("#endif\n")
            output.write("#endif\n")
        return True
    if file == "python_accessor" and r_type != "void" and not r_field:
        # Those have been manually generated
        if cond:
            include.write("#endif\n")
            export.write("#endif\n")
            output.write("#endif\n")
        return True

    output.write("PyObject *\n")
    output.write("%s_%s(PyObject *self ATTRIBUTE_UNUSED," % (package, name))
    output.write(" PyObject *args")
    if format == "":
        output.write(" ATTRIBUTE_UNUSED")
    output.write(") {\n")
    if r_type != 'void':
        output.write("    PyObject *py_retval;\n")
    if c_return:
        output.write(c_return)
    if c_args:
        output.write(c_args)
    if format:
        output.write("\n    if (!PyArg_ParseTuple(args, (char *)\"%s\"%s))\n" %
                     (format, format_args))
        output.write("        return NULL;\n")
    if c_convert:
        output.write(c_convert + "\n")

    output.write("    LIBVIRT_BEGIN_ALLOW_THREADS;")
    output.write(c_call)
    output.write("    LIBVIRT_END_ALLOW_THREADS;\n")
    output.write(ret_convert)
    output.write("}\n\n")
    if cond:
        include.write("#endif /* %s */\n" % cond)
        export.write("#endif /* %s */\n" % cond)
        output.write("#endif /* %s */\n" % cond)

    return True


def print_c_pointer(classname: str, output: IO[str], export: IO[str], include: IO[str]) -> None:
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


def load_apis(module: str, api_xml: str):
    global onlyOverrides

    try:
        onlyOverrides = False
        with open(api_xml) as stream:
            parse(stream)
    except IOError as msg:
        print(api_xml, ":", msg)
        sys.exit(1)

    n = len(functions)
    if not quiet:
        print("Found %d functions in %s" % ((n), api_xml))

    override_api_xml = "%s-override-api.xml" % module
    py_types['pythonObject'] = ('O', "pythonObject", "pythonObject", "pythonObject")

    try:
        onlyOverrides = True
        with openSourceFile(override_api_xml) as stream:
            parse(stream)
    except IOError as msg:
        print(override_api_xml, ":", msg)

    if not quiet:
        # XXX: This is not right, same function already in @functions
        # will be overwritten.
        print("Found %d functions in %s" % (len(functions) - n, override_api_xml))


def emit_c_code(module: str) -> None:
    package = module.replace('-', '_')

    nb_wrap = 0

    header_file = "%s/%s.h" % (buildDir, module)
    export_file = "%s/%s-export.c.inc" % (buildDir, module)
    wrapper_file = "%s/%s.c" % (buildDir, module)

    include = open(header_file, "w")
    include.write("/* Generated by generator.py */\n\n")

    export = open(export_file, "w")
    export.write("/* Generated by generator.py */\n\n")

    wrapper = open(wrapper_file, "w")
    wrapper.write("/* Generated by generator.py */\n\n")
    wrapper.write("#include <stdlib.h>\n")
    wrapper.write("#include <Python.h>\n")
    wrapper.write("#include <libvirt/%s.h>\n" % (module,))
    wrapper.write("#include \"typewrappers.h\"\n")
    wrapper.write("#include \"%s.h\"\n\n" % (module))

    for function in sorted(functions):
        if print_function_wrapper(package, function, wrapper, export, include):
            nb_wrap += 1

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


#######################################################################
#
#  This part writes part of the Python front-end classes based on
#  mapping rules between types and classes and also based on function
#  renaming to get consistent function names at the Python level
#
#######################################################################

#
# The type automatically remapped to generated classes
# "C-type" -> (accessor, create, class, parent-class)
#
classes_type = {
    "virDomainPtr": ("._o", "virDomain(%(p)s, _obj=%(o)s)", "virDomain", "virConnect"),
    "virDomain *": ("._o", "virDomain(%(p)s, _obj=%(o)s)", "virDomain", "virConnect"),
    "virNetworkPtr": ("._o", "virNetwork(%(p)s, _obj=%(o)s)", "virNetwork", "virConnect"),
    "virNetwork *": ("._o", "virNetwork(%(p)s, _obj=%(o)s)", "virNetwork", "virConnect"),
    "virNetworkPortPtr": ("._o", "virNetworkPort(%(p)s, _obj=%(o)s)", "virNetworkPort", "virNetwork"),
    "virNetworkPort *": ("._o", "virNetworkPort(%(p)s, _obj=%(o)s)", "virNetworkPort", "virNetwork"),
    "virInterfacePtr": ("._o", "virInterface(%(p)s, _obj=%(o)s)", "virInterface", "virConnect"),
    "virInterface *": ("._o", "virInterface(%(p)s, _obj=%(o)s)", "virInterface", "virConnect"),
    "virStoragePoolPtr": ("._o", "virStoragePool(%(p)s, _obj=%(o)s)", "virStoragePool", "virConnect"),
    "virStoragePool *": ("._o", "virStoragePool(%(p)s, _obj=%(o)s)", "virStoragePool", "virConnect"),
    "virStorageVolPtr": ("._o", "virStorageVol(%(p)s, _obj=%(o)s)", "virStorageVol", "virConnect"),
    "virStorageVol *": ("._o", "virStorageVol(%(p)s, _obj=%(o)s)", "virStorageVol", "virConnect"),
    "virNodeDevicePtr": ("._o", "virNodeDevice(%(p)s, _obj=%(o)s)", "virNodeDevice", "virConnect"),
    "virNodeDevice *": ("._o", "virNodeDevice(%(p)s, _obj=%(o)s)", "virNodeDevice", "virConnect"),
    "virSecretPtr": ("._o", "virSecret(%(p)s, _obj=%(o)s)", "virSecret", "virConnect"),
    "virSecret *": ("._o", "virSecret(%(p)s, _obj=%(o)s)", "virSecret", "virConnect"),
    "virNWFilterPtr": ("._o", "virNWFilter(%(p)s, _obj=%(o)s)", "virNWFilter", "virConnect"),
    "virNWFilter *": ("._o", "virNWFilter(%(p)s, _obj=%(o)s)", "virNWFilter", "virConnect"),
    "virNWFilterBindingPtr": ("._o", "virNWFilterBinding(%(p)s, _obj=%(o)s)", "virNWFilterBinding", "virConnect"),
    "virNWFilterBinding *": ("._o", "virNWFilterBinding(%(p)s, _obj=%(o)s)", "virNWFilterBinding", "virConnect"),
    "virStreamPtr": ("._o", "virStream(%(p)s, _obj=%(o)s)", "virStream", "virConnect"),
    "virStream *": ("._o", "virStream(%(p)s, _obj=%(o)s)", "virStream", "virConnect"),
    "virConnectPtr": ("._o", "virConnect(_obj=%(o)s)", "virConnect", ""),
    "virConnect *": ("._o", "virConnect(_obj=%(o)s)", "virConnect", ""),
    "virDomainCheckpointPtr": ("._o", "virDomainCheckpoint(%(p)s, _obj=%(o)s)", "virDomainCheckpoint", "virDomain"),
    "virDomainCheckpoint *": ("._o", "virDomainCheckpoint(%(p)s, _obj=%(o)s)", "virDomainCheckpoint", "virDomain"),
    "virDomainSnapshotPtr": ("._o", "virDomainSnapshot(%(p)s, _obj=%(o)s)", "virDomainSnapshot", "virDomain"),
    "virDomainSnapshot *": ("._o", "virDomainSnapshot(%(p)s, _obj=%(o)s)", "virDomainSnapshot", "virDomain"),
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
    "virNodeDevice": "virNodeDeviceFree",
    "virSecret": "virSecretFree",
    "virNWFilter": "virNWFilterFree",
    "virNWFilterBinding": "virNWFilterBindingFree",
    "virDomainCheckpoint": "virDomainCheckpointFree",
    "virDomainSnapshot": "virDomainSnapshotFree",
    # We hand-craft __del__ for this one
    # "virStream": "virStreamFree",
}

class_skip_connect_impl = {
    "virConnect",
}

class_domain_impl = {
    "virDomainCheckpoint",
    "virDomainSnapshot",
}

class_network_impl = {
    "virNetworkPort",
}

functions_noexcept = {
    'virDomainGetID',
    'virDomainGetName',
    'virNetworkGetName',
    'virInterfaceGetName',
    'virStoragePoolGetName',
    'virStorageVolGetName',
    'virStorageVolGetkey',
    'virNodeDeviceGetName',
    'virNodeDeviceGetParent',
    'virSecretGetUsageType',
    'virSecretGetUsageID',
    'virNWFilterGetName',
    'virNWFilterBindingGetFilterName',
    'virNWFilterBindingGetPortDev',
}

function_classes = {
    "None": []
}  # type: Dict[str, List[Tuple[int, str, str, ArgumentType, List[ArgumentType], str, str]]]

# Functions returning an integral type which need special rules to
# check for errors and raise exceptions.
functions_int_exception_test = {
    'virDomainGetMaxMemory': "%s == 0",
}
functions_int_default_test = "%s == -1"


def is_integral_type(name: str) -> bool:
    return re.search("^(unsigned)? ?(int|long)$", name) is not None


def is_optional_arg(info: str) -> bool:
    return re.search(r"^\(?optional\)?", info) is not None


def is_python_noninteger_type(name: str) -> bool:
    return name[-1:] == "*"


def nameFixup(name: str, classe: str, type: str, file: str) -> str:
    # avoid a disastrous clash
    listname = classe + "List"
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
    elif name[0:16] == "virNodeDeviceGet":
        func = name[16].lower() + name[17:]
    elif name[0:19] == "virNodeDeviceLookup":
        func = name[3].lower() + name[4:]
    elif name[0:22] == "virNodeDeviceCreateXML":
        func = name[3].lower() + name[4:]
    elif name[0:19] == "virNodeDeviceDefine":
        func = name[3].lower() + name[4:]
    elif name[0:13] == "virNodeDevice":
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


def functionSortKey(info: Tuple) -> Tuple[str, str]:
    (index, func, name, ret, args, filename, mod) = info
    return func, filename


def writeDoc(module: str, name: str, args: List[ArgumentType], indent: str, output: IO) -> None:
    if not functions[name][0]:
        return
    val = functions[name][0]
    val = val.replace("NULL", "None")
    sep = '\n%s' % (indent,)
    output.write('%s"""%s """\n' % (indent, sep.join(val.splitlines())))


def emit_py_code(module: str) -> None:
    package = module.replace('-', '_')
    if module == "libvirt":
        pymod = "libvirtmod"
        cygmod = "cygvirtmod"
    elif module == "libvirt-lxc":
        pymod = "libvirtmod_lxc"
        cygmod = "cygvirtmod_lxc"
    elif module == "libvirt-qemu":
        pymod = "libvirtmod_qemu"
        cygmod = "cygvirtmod_qemu"
    else:
        raise Exception("Unknown module '%s'" % module)

    for tinfo in classes_type.values():
        function_classes[tinfo[2]] = []

    #
    # Build the list of C types to look for ordered to start
    # with primary classes
    #
    ctypes = []  # type: List[str]
    classes_list = []  # type: List[str]
    ctypes_processed = set()  # type: Set[str]
    classes_processed = set()  # type: Set[str]
    for classe in primary_classes:
        classes_list.append(classe)
        classes_processed.add(classe)
        for type, tinfo in classes_type.items():
            if tinfo[2] == classe:
                ctypes.append(type)
                ctypes_processed.add(type)
    for type, tinfo in classes_type.items():
        if type in ctypes_processed:
            continue
        if tinfo[2] not in classes_processed:
            classes_list.append(tinfo[2])
            classes_processed.add(tinfo[2])

        ctypes.append(type)
        ctypes_processed.add(type)

    for name, (desc, ret, args, file, mod, cond) in functions.items():
        if skip_py_impl(name):
            continue

        for type in ctypes:
            classe = classes_type[type][2]

            if name[0:3] == "vir" and len(args) >= 1 and args[0][1] == type:
                func = nameFixup(name, classe, type, file)
                info = (0, func, name, ret, args, file, mod)
                function_classes[classe].append(info)
                break
            elif name[0:3] == "vir" and len(args) >= 2 and args[1][1] == type \
                    and file != "python_accessor" and name not in function_skip_index_one:
                func = nameFixup(name, classe, type, file)
                info = (1, func, name, ret, args, file, mod)
                function_classes[classe].append(info)
                break
        else:
            func = nameFixup(name, "None", file, file)
            info = (0, func, name, ret, args, file, mod)
            function_classes['None'].append(info)

    classes_file = "%s/%s.py" % (buildDir, package)
    extra_file = "%s-override.py" % module
    extra = openSourceFile(extra_file, "r", True)

    classes = open(classes_file, "w")

    classes.write("#\n")
    classes.write("# WARNING WARNING WARNING WARNING\n")
    classes.write("#\n")
    classes.write("# This file is automatically written by generator.py. Any changes\n")
    classes.write("# made here will be lost.\n")
    classes.write("#\n")
    classes.write("# To change the manually written methods edit %s-override.py\n" % (module,))
    classes.write("# To change the automatically written methods edit generator.py\n")
    classes.write("#\n")
    classes.write("# WARNING WARNING WARNING WARNING\n")
    classes.write("#\n")
    classes.write("try:\n")
    classes.write("    import %s  # type: ignore\n" % pymod)
    classes.write("except ImportError as lib_e:\n")
    classes.write("    try:\n")
    classes.write("        import %s as %s  # type: ignore\n" % (cygmod, pymod))
    classes.write("    except ImportError as cyg_e:\n")
    classes.write("        if \"No module named\" in str(cyg_e):\n")
    classes.write("            raise lib_e\n\n")

    if module != "libvirt":
        classes.write("import libvirt\n")
        classes.write("\n")

    if extra:
        classes.write("# WARNING WARNING WARNING WARNING\n")
        classes.write("#\n")
        classes.write("# Manually written part of python bindings for %s\n" % module)
        classes.writelines(extra.readlines())
    classes.write("#\n")
    classes.write("# WARNING WARNING WARNING WARNING\n")
    classes.write("#\n")
    classes.write("# Automatically written part of python bindings for %s\n" % module)
    classes.write("#\n")
    classes.write("# WARNING WARNING WARNING WARNING\n")
    if extra:
        extra.close()

    if "None" in function_classes:
        flist = function_classes["None"]
        oldfile = ""
        for (index, func, name, ret, args, file, mod) in sorted(flist, key=functionSortKey):
            if file != oldfile:
                classes.write("#\n# Functions from module %s\n#\n\n" % file)
                oldfile = file
            classes.write("def %s(" % func)
            for n, (a_name, a_type, a_info) in enumerate(args):
                if n != 0:
                    classes.write(", ")
                classes.write("%s" % a_name)
                if a_name == "flags" or is_optional_arg(a_info):
                    if is_integral_type(a_type):
                        classes.write("=0")
                    else:
                        classes.write("=None")
            classes.write("):\n")
            writeDoc(module, name, args, '    ', classes)

            for a_name, a_type, a_info in args:
                if a_type in classes_type:
                    classes.write("    if %s is None:\n"
                                  "        %s__o = None\n" %
                                  (a_name, a_name))
                    classes.write("    else:\n"
                                  "        %s__o = %s%s\n" %
                                  (a_name, a_name, classes_type[a_type][0]))

            r_type, r_info, r_field = ret
            if r_type != "void":
                classes.write("    ret = ")
            else:
                classes.write("    ")
            classes.write("%s.%s(" % (pymod, name))
            for n, (a_name, a_type, a_info) in enumerate(args):
                if n != 0:
                    classes.write(", ")
                classes.write("%s" % a_name)
                if a_type in classes_type:
                    classes.write("__o")
            classes.write(")\n")

            if r_type != "void":
                if r_type in classes_type:
                    #
                    # Raise an exception
                    #
                    if name in functions_noexcept:
                        classes.write("    if ret is None:\n"
                                      "        return None\n")
                    else:
                        classes.write(
                            "    if ret is None:\n"
                            "        raise libvirtError('%s() failed')\n" %
                            (name))

                    tinfo = classes_type[r_type]
                    classes.write("    return ")
                    classes.write(tinfo[1] % {"o": "ret"})
                    classes.write("\n")

                # For functions returning an integral type there are
                # several things that we can do, depending on the
                # contents of functions_int_*:
                elif is_integral_type(r_type):
                    if name not in functions_noexcept:
                        test = functions_int_exception_test.get(name, functions_int_default_test) % ("ret",)
                        classes.write(
                            "    if %s:\n"
                            "        raise libvirtError('%s() failed')\n" %
                            (test, name))
                    classes.write("    return ret\n")

                elif is_python_noninteger_type(r_type):
                    if name not in functions_noexcept:
                        classes.write(
                            "    if ret is None:\n"
                            "        raise libvirtError('%s() failed')\n" %
                            (name,))
                    classes.write("    return ret\n")

                else:
                    classes.write("    return ret\n")

            classes.write("\n")

    modclasses = []
    if module == "libvirt":
        modclasses = classes_list
    for classname in modclasses:
        PARENTS = {
            "virConnect": "self._conn",
            "virDomain": "self._dom",
            "virNetwork": "self._net",
            classname: "self",
        }

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
            if classname in ["virDomain", "virNetwork", "virInterface", "virStoragePool",
                             "virStorageVol", "virNodeDevice", "virSecret", "virStream",
                             "virNWFilter", "virNWFilterBinding"]:
                classes.write("    def __init__(self, conn, _obj=None):\n")
                classes.write("        self._conn = conn\n")
            elif classname in ["virDomainCheckpoint", "virDomainSnapshot"]:
                classes.write("    def __init__(self, dom, _obj=None):\n")
                classes.write("        self._dom = dom\n")
                classes.write("        self._conn = dom.connect()\n")
            elif classname in ["virNetworkPort"]:
                classes.write("    def __init__(self, net, _obj=None) -> None:\n")
                classes.write("        self._net = net\n")
                classes.write("        self._conn = net.connect()\n")
            else:
                classes.write("    def __init__(self, _obj=None):\n")

            classes.write("        if type(_obj).__name__ not in [\"PyCapsule\", \"PyCObject\"]:\n")
            classes.write("            raise Exception(\"Expected a wrapped C Object but got %s\" % type(_obj))\n")
            classes.write("        self._o = _obj\n\n")
            destruct = None
            if classname in classes_destructors:
                classes.write("    def __del__(self):\n")
                classes.write("        if self._o is not None:\n")
                classes.write("            %s.%s(self._o)\n" %
                              (pymod, classes_destructors[classname]))
                classes.write("        self._o = None\n\n")
                destruct = classes_destructors[classname]

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
            classes.write("        return %s.%s_pointer(self._o)\n\n" %
                          (pymod, classname))

            flist = function_classes[classname]
            oldfile = ""
            for (index, func, name, ret, args, file, mod) in sorted(flist, key=functionSortKey):
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
                for n, (a_name, a_type, a_info) in enumerate(args):
                    if n != index:
                        classes.write(", %s" % a_name)
                    if a_name == "flags" or is_optional_arg(a_info):
                        if is_integral_type(a_type):
                            classes.write("=0")
                        else:
                            classes.write("=None")
                classes.write("):\n")
                writeDoc(module, name, args, '        ', classes)
                for n, (a_name, a_type, a_info) in enumerate(args):
                    if a_type in classes_type:
                        if n != index:
                            classes.write("        if %s is None:\n"
                                          "            %s__o = None\n" %
                                          (a_name, a_name))
                            classes.write("        else:\n"
                                          "            %s__o = %s%s\n" %
                                          (a_name, a_name, classes_type[a_type][0]))
                r_type, r_info, r_field = ret
                if r_type != "void":
                    classes.write("        ret = ")
                else:
                    classes.write("        ")
                classes.write("%s.%s(" % (pymod, name))
                for n, (a_name, a_type, a_info) in enumerate(args):
                    if n != 0:
                        classes.write(", ")
                    if n != index:
                        classes.write("%s" % a_name)
                        if a_type in classes_type:
                            classes.write("__o")
                    else:
                        classes.write("self")
                        if a_type in classes_type:
                            classes.write(classes_type[a_type][0])
                classes.write(")\n")

                if name == "virConnectClose":
                    classes.write("        self._o = None\n")

                # For functions returning object types:
                if r_type != "void":
                    if r_type in classes_type:
                        #
                        # Raise an exception
                        #
                        if name in functions_noexcept:
                            classes.write(
                                "        if ret is None:\n"
                                "            return None\n")
                        else:
                            classes.write(
                                "        if ret is None:\n"
                                "            raise libvirtError('%s() failed')\n" %
                                (name,))

                        #
                        # generate the returned class wrapper for the object
                        #
                        tinfo = classes_type[r_type]
                        classes.write("        __tmp = ")
                        classes.write(tinfo[1] % {"o": "ret", "p": PARENTS[tinfo[3]]})
                        classes.write("\n")

                        #
                        # return the class
                        #
                        classes.write("        return __tmp\n")

                    # For functions returning an integral type there
                    # are several things that we can do, depending on
                    # the contents of functions_int_*:
                    elif is_integral_type(r_type):
                        if name not in functions_noexcept:
                            test = functions_int_exception_test.get(name, functions_int_default_test) % ("ret",)
                            classes.write(
                                "        if %s:\n"
                                "            raise libvirtError('%s() failed')\n" %
                                (test, name))

                        classes.write("        return ret\n")

                    elif is_python_noninteger_type(r_type):
                        if name not in functions_noexcept:
                            classes.write(
                                "        if ret is None:\n"
                                "            raise libvirtError('%s() failed')\n" %
                                (name,))

                        classes.write("        return ret\n")
                    else:
                        classes.write("        return ret\n")

                classes.write("\n")
            # Append "<classname>.py" to class def, iff it exists
            class_override = "%s-override-%s.py" % (module, classname)
            extra = openSourceFile(class_override, "r", True)
            if extra:
                classes.write("    #\n")
                classes.write("    # %s methods from %s.py (hand coded)\n" % (classname, classname))
                classes.write("    #\n")
                cached = None

                # Since we compile with older libvirt, we don't want to pull
                # in manually written python methods which call C methods
                # that don't exist. This code attempts to detect which
                # methods to skip by looking at the libvirtmod.XXXX calls

                def shouldSkip(lines: List[str]) -> bool:
                    for line in lines:
                        offset = line.find(pymod + ".")
                        if offset != -1:
                            func = line[offset + 11:]
                            offset = func.find("(")
                            func = func[0:offset]
                            if not skip_c_impl(func) and func != "virConnectListDomains":
                                return True
                    return False

                for line in extra.readlines():
                    offset = line.find(" def ")
                    if offset != -1:
                        name = line[offset + 5:]
                        offset = name.find("(")
                        name = name[0:offset]
                        if cached:
                            if not shouldSkip(cached):
                                classes.writelines(cached)
                        if name == "__del__":
                            cached = None
                            classes.write(line)
                        else:
                            cached = [line]
                    else:
                        if cached:
                            cached.append(line)
                        else:
                            classes.write(line)
                if cached is not None and not shouldSkip(cached):
                    classes.writelines(cached)
                classes.write("\n")
                extra.close()

    direct_functions = {}
    if module != "libvirt":
        direct_functions = functions

        classes.write("#\n# Functions from module %s\n#\n\n" % module)

    #
    # Generate functions directly, no classes
    #
    for name, (desc, ret, args, file, mod, cond) in sorted(direct_functions.items()):
        if skip_py_impl(name):
            continue
        func = nameFixup(name, 'None', '', '')
        classes.write("def %s(" % func)
        for n, (a_name, a_type, a_info) in enumerate(args):
            if n != 0:
                classes.write(", ")
            classes.write("%s" % a_name)
        classes.write("):\n")
        writeDoc(module, name, args, '    ', classes)

        r_type, r_info, r_field = ret
        if r_type != "void":
            classes.write("    ret = ")
        else:
            classes.write("    ")
        classes.write("%s.%s(" % (pymod, name))

        conn = None

        for n, (a_name, a_type, a_info) in enumerate(args):
            if a_type == "virConnectPtr":
                conn = a_name

            if n != 0:
                classes.write(", ")
            if a_type in ["virDomainPtr", "virConnectPtr"]:
                # FIXME: This might have problem if the function
                # has multiple args which are objects.
                classes.write("%s.%s" % (a_name, "_o"))
            else:
                classes.write("%s" % a_name)
        classes.write(")\n")

        if r_type != "void":
            classes.write("    if ret is None:\n"
                     "        raise libvirt.libvirtError('%s() failed')\n" % (name,))
            if r_type == "virDomainPtr":
                classes.write("    __tmp = libvirt.virDomain(%s, _obj=ret)\n" % (conn,))
                classes.write("    return __tmp\n")
            else:
                classes.write("    return ret\n")

        classes.write("\n")

    #
    # Generate enum constants
    #
    def enumsSortKey(data: Tuple[str, EnumValue]) -> Tuple[Union[int, float], str]:
        try:
            value = int(data[1])  # type: Union[int, float]
        except ValueError:
            value = float('inf')
        return value, data[0]

    # Resolve only one level of reference
    def resolveEnum(enum: EnumType, data: EnumType) -> EnumType:
        for name, val in enum.items():
            try:
                int(val)
            except ValueError:
                enum[name] = data[val]  # type: ignore
        return enum

    enumvals = list(enums.items())
    # convert list of dicts to one dict
    enumData = {}  # type: EnumType
    for type, enum in enumvals:
        enumData.update(enum)

    for type, enum in sorted(enumvals):
        classes.write("# %s\n" % type)
        items = sorted(resolveEnum(enum, enumData).items(), key=enumsSortKey)
        if items[-1][0].endswith('_LAST'):
            del items[-1]
        for name, value in items:
            classes.write("%s = %s\n" % (name, value))
        classes.write("\n")

    if params:
        classes.write("# typed parameter names\n")
        for name, value in params:
            classes.write("%s = \"%s\"\n" % (name, value))

    classes.close()

if sys.argv[1] not in ["libvirt", "libvirt-lxc", "libvirt-qemu"]:
    print("ERROR: unknown module %s" % sys.argv[1])
    sys.exit(1)

if len(sys.argv) == 6:
    buildDir = sys.argv[5]
if len(sys.argv) >= 5:
    sourceDir = sys.argv[4]

load_apis(sys.argv[1], sys.argv[2])

if validate_functions() < 0:
    sys.exit(1)

quiet = False
if not os.path.exists(buildDir):
    os.mkdir(buildDir)

output = None
if len(sys.argv) >= 4:
    output = sys.argv[3]
if output == "c" or output == "c+py" or output is None:
    emit_c_code(sys.argv[1])

if output == "py" or output == "c+py" or output is None:
    emit_py_code(sys.argv[1])

sys.exit(0)
