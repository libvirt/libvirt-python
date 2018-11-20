#!/usr/bin/env python3
# Print some host NUMA node statistics
#
# Authors:
#   Michal Privoznik <mprivozn@redhat.com>

import libvirt
from xml.dom import minidom
import libxml2
from typing import Any, Dict  # noqa F401


def xpath_eval(ctxt, path: str) -> str:
    res = ctxt.xpathEval(path)
    if res is None or len(res) == 0:
        value = ''
    else:
        value = res[0].content
    return value


try:
    conn = libvirt.openReadOnly(None)
except libvirt.libvirtError:
    print("Failed to connect to the hypervisor")
    exit(1)

try:
    capsXML = conn.getCapabilities()
except libvirt.libvirtError:
    print("Failed to request capabilities")
    exit(1)

caps = minidom.parseString(capsXML)
cells = caps.getElementsByTagName("cells")[0]

nodesIDs = [
    int(proc.getAttribute("id"))
    for proc in cells.getElementsByTagName("cell")
]

nodesMem = [
    conn.getMemoryStats(int(proc))
    for proc in nodesIDs
]

doms = conn.listAllDomains(libvirt.VIR_CONNECT_LIST_DOMAINS_ACTIVE)

domsStrict = [
    proc
    for proc in doms
    if proc.numaParameters()["numa_mode"] == libvirt.VIR_DOMAIN_NUMATUNE_MEM_STRICT
]

domsStrictCfg = {}  # type: Dict[libvirt.virDomain, Dict[str, Dict[str, Any]]]
for dom in domsStrict:
    xmlStr = dom.XMLDesc()
    doc = libxml2.parseDoc(xmlStr)
    ctxt = doc.xpathNewContext()

    domsStrictCfg[dom] = {}

    pin = ctxt.xpathEval("string(/domain/numatune/memory/@nodeset)")
    memsize = ctxt.xpathEval("string(/domain/memory)")
    domsStrictCfg[dom]["memory"] = {"size": int(memsize), "pin": pin}

    for memnode in ctxt.xpathEval("/domain/numatune/memnode"):
        ctxt.setContextNode(memnode)
        cellid = xpath_eval(ctxt, "@cellid")
        nodeset = xpath_eval(ctxt, "@nodeset")

        nodesize = xpath_eval(ctxt, "/domain/cpu/numa/cell[@id='%s']/@memory" % cellid)
        domsStrictCfg[dom][cellid] = {"size": int(nodesize), "pin": nodeset}


print("NUMA stats")
print("NUMA nodes:\t" + "\t".join(str(node) for node in nodesIDs))
print("MemTotal:\t" + "\t".join(str(i.get("total") // 1024) for i in nodesMem))  # type: ignore
print("MemFree:\t" + "\t".join(str(i.get("free") // 1024) for i in nodesMem))  # type: ignore

for dom, v in domsStrictCfg.items():
    print("Domain '%s':\t" % dom.name())

    toPrint = "\tOverall memory: %d MiB" % (v["memory"]["size"] // 1024)
    if v["memory"]["pin"] is not None and v["memory"]["pin"] != "":
        toPrint = toPrint + " nodes %s" % v["memory"]["pin"]
    print(toPrint)

    for k, node in sorted(v.items()):
        if k == "memory":
            continue
        toPrint = "\tNode %s:\t%d MiB" % (k, node["size"] // 1024)
        if node["pin"] is not None and node["pin"] == "":
            toPrint = toPrint + " nodes %s" % node["pin"]
        print(toPrint)
