#!/usr/bin/env python

import sys
import lxml
import lxml.etree
import string

if len(sys.argv) >= 2:
    # Munge import path to insert build location for libvirt mod
    sys.path.insert(0, sys.argv[1])
import libvirt

if sys.version > '3':
    long = int

def get_libvirt_api_xml_path():
    import subprocess
    args = ["pkg-config", "--variable", "libvirt_api", "libvirt"]
    proc = subprocess.Popen(args, stdout=subprocess.PIPE)
    stdout, _ = proc.communicate()
    if proc.returncode:
        sys.exit(proc.returncode)
    return stdout.splitlines()[0]

# Path to the libvirt API XML file
if len(sys.argv) >= 3:
    xml = sys.argv[2]
else:
    xml = get_libvirt_api_xml_path()

with open(xml, "r") as fp:
    tree = lxml.etree.parse(fp)

verbose = False
fail = False

enumvals = {}
second_pass = []
wantenums = []
wantfunctions = []

# Phase 1: Identify all functions and enums in public API
set = tree.xpath('/api/files/file/exports[@type="function"]/@symbol')
for n in set:
    wantfunctions.append(n)

set = tree.xpath('/api/symbols/enum')
for n in set:
    typ = n.attrib['type']
    name = n.attrib['name']
    val = n.attrib['value']

    if typ not in enumvals:
        enumvals[typ] = {}

    # If the value cannot be converted to int, it is reference to
    # another enum and needs to be sorted out later on
    try:
        val = int(val)
    except ValueError:
        second_pass.append(n)
        continue

    enumvals[typ][name] = int(val)

for n in second_pass:
    typ = n.attrib['type']
    name = n.attrib['name']
    val = n.attrib['value']

    for v in enumvals.values():
        if val in v:
            val = int(v[val])
            break

    if type(val) != int:
        fail = True
        print("Cannot get a value of enum %s (originally %s)" % (val, name))
    enumvals[typ][name] = val

set = tree.xpath('/api/files/file/exports[@type="enum"]/@symbol')
for n in set:
    for enumval in enumvals.values():
        if n in enumval:
            enum = enumval
            break
    # Eliminate sentinels
    if n.endswith('_LAST') and enum[n] == max(enum.values()):
        continue
    wantenums.append(n)

# Phase 2: Identify all classes and methods in the 'libvirt' python module
gotenums = []
gottypes = []
gotfunctions = { "libvirt": [] }

for name in dir(libvirt):
    if name[0] == '_':
        continue
    thing = getattr(libvirt, name)
    # Special-case libvirtError to deal with python 2.4 difference
    # in Exception class type reporting.
    if type(thing) in (int, long):
        gotenums.append(name)
    elif type(thing) == type or name == "libvirtError":
        gottypes.append(name)
        gotfunctions[name] = []
    elif callable(thing):
        gotfunctions["libvirt"].append(name)
    else:
       pass

for enum in wantenums:
    if enum not in gotenums:
        fail = True
        for typ, enumval in enumvals.items():
            if enum in enumval:
                print("FAIL Missing exported enum %s of type %s" % (enum, typ))

for klassname in gottypes:
    klassobj = getattr(libvirt, klassname)
    for name in dir(klassobj):
        if name[0] == '_':
            continue
        if name == 'c_pointer':
            continue
        thing = getattr(klassobj, name)
        if callable(thing):
            gotfunctions[klassname].append(name)
        else:
            pass


# Phase 3: First cut at mapping of C APIs to python classes + methods
basicklassmap = {}

for cname in wantfunctions:
    name = cname
    # Some virConnect APIs have stupid names
    if name[0:7] == "virNode" and name[0:13] != "virNodeDevice":
        name = "virConnect" + name[7:]
    if name[0:7] == "virConn" and name[0:10] != "virConnect":
        name = "virConnect" + name[7:]

    # The typed param APIs are only for internal use
    if name[0:14] == "virTypedParams":
        continue

    if name[0:23] == "virNetworkDHCPLeaseFree":
        continue

    if name[0:28] == "virDomainStatsRecordListFree":
        continue

    if name[0:19] == "virDomainFSInfoFree":
        continue

    if name[0:25] == "virDomainIOThreadInfoFree":
        continue

    if name[0:22] == "virDomainInterfaceFree":
        continue

    if name[0:21] == "virDomainListGetStats":
        name = "virConnectDomainListGetStats"

    # These aren't functions, they're callback signatures
    if name in ["virConnectAuthCallbackPtr", "virConnectCloseFunc",
                "virStreamSinkFunc", "virStreamSourceFunc", "virStreamEventCallback",
                "virEventHandleCallback", "virEventTimeoutCallback", "virFreeCallback",
                "virStreamSinkHoleFunc", "virStreamSourceHoleFunc", "virStreamSourceSkipFunc"]:
        continue
    if name[0:21] == "virConnectDomainEvent" and name[-8:] == "Callback":
        continue
    if name[0:22] == "virConnectNetworkEvent" and name[-8:] == "Callback":
        continue
    if (name.startswith("virConnectStoragePoolEvent") and
        name.endswith("Callback")):
        continue
    if (name.startswith("virConnectNodeDeviceEvent") and
        name.endswith("Callback")):
        continue
    if (name.startswith("virConnectSecretEvent") and
        name.endswith("Callback")):
        continue


    # virEvent APIs go into main 'libvirt' namespace not any class
    if name[0:8] == "virEvent":
        if name[-4:] == "Func":
            continue
        basicklassmap[name] = ["libvirt", name, cname]
    else:
        found = False
        # To start with map APIs to classes based on the
        # naming prefix. Mistakes will be fixed in next
        # loop
        for klassname in gottypes:
            klen = len(klassname)
            if name[0:klen] == klassname:
                found = True
                if name not in basicklassmap:
                    basicklassmap[name] = [klassname, name[klen:], cname]
                elif len(basicklassmap[name]) < klen:
                    basicklassmap[name] = [klassname, name[klen:], cname]

        # Anything which can't map to a class goes into the
        # global namespaces
        if not found:
            basicklassmap[name] = ["libvirt", name[3:], cname]


# Phase 4: Deal with oh so many special cases in C -> python mapping
finalklassmap = {}

for name in sorted(basicklassmap):
    klass = basicklassmap[name][0]
    func = basicklassmap[name][1]
    cname = basicklassmap[name][2]

    # The object lifecycle APIs are irrelevant since they're
    # used inside the object constructors/destructors.
    if func in ["Ref", "Free", "New", "GetConnect", "GetDomain"]:
        if klass == "virStream" and func == "New":
            klass = "virConnect"
            func = "NewStream"
        else:
            continue


    # All the error handling methods need special handling
    if klass == "libvirt":
        if func in ["CopyLastError", "DefaultErrorFunc",
                    "ErrorFunc", "FreeError",
                    "SaveLastError", "ResetError"]:
            continue
        elif func in ["GetLastError", "GetLastErrorMessage", "ResetLastError", "Initialize"]:
            func = "vir" + func
        elif func == "SetErrorFunc":
            func = "RegisterErrorHandler"
    elif klass == "virConnect":
        if func in ["CopyLastError", "SetErrorFunc"]:
            continue
        elif func in ["GetLastError", "ResetLastError"]:
            func = "virConn" + func

    # Remove 'Get' prefix from most APIs, except those in virConnect
    # and virDomainSnapshot namespaces which stupidly used a different
    # convention which we now can't fix without breaking API
    if func[0:3] == "Get" and klass not in ["virConnect", "virDomainSnapshot", "libvirt"]:
        if func not in ["GetCPUStats", "GetTime"]:
            func = func[3:]

    # The object creation and lookup APIs all have to get re-mapped
    # into the parent class
    if func in ["CreateXML", "CreateLinux", "CreateXMLWithFiles",
                "DefineXML", "CreateXMLFrom", "LookupByUUID",
                "LookupByUUIDString", "LookupByVolume" "LookupByName",
                "LookupByID", "LookupByName", "LookupByKey", "LookupByPath",
                "LookupByMACString", "LookupByUsage", "LookupByVolume",
                "LookupByTargetPath","LookupSCSIHostByWWN",
                "Restore", "RestoreFlags",
                "SaveImageDefineXML", "SaveImageGetXMLDesc", "DefineXMLFlags"]:
        if klass != "virDomain":
            func = klass[3:] + func

        if klass == "virDomainSnapshot":
            klass = "virDomain"
            func = func[6:]
        elif klass == "virStorageVol" and func in ["StorageVolCreateXMLFrom", "StorageVolCreateXML"]:
            klass = "virStoragePool"
            func = func[10:]
        elif func == "StoragePoolLookupByVolume":
            klass = "virStorageVol"
        elif func == "StorageVolLookupByName":
            klass = "virStoragePool"
        else:
            klass = "virConnect"

    # The open methods get remapped to primary namespace
    if klass == "virConnect" and func in ["Open", "OpenAuth", "OpenReadOnly"]:
        klass = "libvirt"

    # These are inexplicably renamed in the python API
    if func == "ListDomains":
        func = "ListDomainsID"
    elif func == "ListAllNodeDevices":
        func = "ListAllDevices"
    elif func == "ListNodeDevices":
        func = "ListDevices"

    # The virInterfaceChangeXXXX APIs go into virConnect. Stupidly
    # they have lost their 'interface' prefix in names, but we can't
    # fix this name
    if func[0:6] == "Change":
        klass = "virConnect"

    # Need to special case the snapshot APIs
    if klass == "virDomainSnapshot" and func in ["Current", "ListNames", "Num"]:
        klass = "virDomain"
        func = "snapshot" + func

    # Names should start with lowercase letter...
    func = func[0:1].lower() + func[1:]
    if func[0:8] == "nWFilter":
        func = "nwfilter" + func[8:]
    if func[0:8] == "fSFreeze" or func[0:6] == "fSThaw" or func[0:6] == "fSInfo":
        func = "fs" + func[2:]
    if func[0:12] == "iOThreadInfo":
        func = "ioThreadInfo"

    if klass == "virNetwork":
        func = func.replace("dHCP", "DHCP")

    # ...except when they don't. More stupid naming
    # decisions we can't fix
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

    finalklassmap[name] = [klass, func, cname]


# Phase 5: Validate sure that every C API is mapped to a python API
usedfunctions = {}
for name in sorted(finalklassmap):
    klass = finalklassmap[name][0]
    func = finalklassmap[name][1]

    if func in gotfunctions[klass]:
        usedfunctions["%s.%s" % (klass, func)] = 1
        if verbose:
            print("PASS %s -> %s.%s" % (name, klass, func))
    else:
        print("FAIL %s -> %s.%s       (C API not mapped to python)" % (name, klass, func))
        fail = True


# Phase 6: Validate that every python API has a corresponding C API
for klass in gotfunctions:
    if klass == "libvirtError":
        continue
    for func in sorted(gotfunctions[klass]):
        # These are pure python methods with no C APi
        if func in ["connect", "getConnect", "domain", "getDomain",
                    "virEventInvokeFreeCallback",
                    "sparseRecvAll", "sparseSendAll"]:
            continue

        key = "%s.%s" % (klass, func)
        if not key in usedfunctions:
            print("FAIL %s.%s       (Python API not mapped to C)" % (klass, func))
            fail = True
        else:
            if verbose:
                print("PASS %s.%s" % (klass, func))

# Phase 7: Validate that all the low level C APIs have binding
for name in sorted(finalklassmap):
    cname = finalklassmap[name][2]

    pyname = cname
    if pyname == "virSetErrorFunc":
        pyname = "virRegisterErrorHandler"
    elif pyname == "virConnectListDomains":
        pyname = "virConnectListDomainsID"

    # These exist in C and exist in python, but we've got
    # a pure-python impl so don't check them
    if name in ["virStreamRecvAll", "virStreamSendAll",
            "virStreamSparseRecvAll", "virStreamSparseSendAll"]:
        continue

    try:
        thing = getattr(libvirt.libvirtmod, pyname)
    except AttributeError:
        print("FAIL libvirt.libvirtmod.%s      (C binding does not exist)" % pyname)
        fail = True

if fail:
    sys.exit(1)
else:
    sys.exit(0)
