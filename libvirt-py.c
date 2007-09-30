/* Generated */

#include <Python.h>
#include <libvirt/libvirt.h>
#include "libvirt_wrap.h"
#include "libvirt-py.h"

PyObject *
libvirt_virDomainDefineXML(PyObject *self ATTRIBUTE_UNUSED, PyObject *args) {
    PyObject *py_retval;
    virDomainPtr c_retval;
    virConnectPtr conn;
    PyObject *pyobj_conn;
    char * xml;

    if (!PyArg_ParseTuple(args, (char *)"Oz:virDomainDefineXML", &pyobj_conn, &xml))
        return(NULL);
    conn = (virConnectPtr) PyvirConnect_Get(pyobj_conn);
LIBVIRT_BEGIN_ALLOW_THREADS;

    c_retval = virDomainDefineXML(conn, xml);
LIBVIRT_END_ALLOW_THREADS;
    py_retval = libvirt_virDomainPtrWrap((virDomainPtr) c_retval);
    return(py_retval);
}

PyObject *
libvirt_virDomainShutdown(PyObject *self ATTRIBUTE_UNUSED, PyObject *args) {
    PyObject *py_retval;
    int c_retval;
    virDomainPtr domain;
    PyObject *pyobj_domain;

    if (!PyArg_ParseTuple(args, (char *)"O:virDomainShutdown", &pyobj_domain))
        return(NULL);
    domain = (virDomainPtr) PyvirDomain_Get(pyobj_domain);
LIBVIRT_BEGIN_ALLOW_THREADS;

    c_retval = virDomainShutdown(domain);
LIBVIRT_END_ALLOW_THREADS;
    py_retval = libvirt_intWrap((int) c_retval);
    return(py_retval);
}

PyObject *
libvirt_virDomainLookupByUUIDString(PyObject *self ATTRIBUTE_UNUSED, PyObject *args) {
    PyObject *py_retval;
    virDomainPtr c_retval;
    virConnectPtr conn;
    PyObject *pyobj_conn;
    char * uuidstr;

    if (!PyArg_ParseTuple(args, (char *)"Oz:virDomainLookupByUUIDString", &pyobj_conn, &uuidstr))
        return(NULL);
    conn = (virConnectPtr) PyvirConnect_Get(pyobj_conn);
LIBVIRT_BEGIN_ALLOW_THREADS;

    c_retval = virDomainLookupByUUIDString(conn, uuidstr);
LIBVIRT_END_ALLOW_THREADS;
    py_retval = libvirt_virDomainPtrWrap((virDomainPtr) c_retval);
    return(py_retval);
}

PyObject *
libvirt_virConnectNumOfDefinedNetworks(PyObject *self ATTRIBUTE_UNUSED, PyObject *args) {
    PyObject *py_retval;
    int c_retval;
    virConnectPtr conn;
    PyObject *pyobj_conn;

    if (!PyArg_ParseTuple(args, (char *)"O:virConnectNumOfDefinedNetworks", &pyobj_conn))
        return(NULL);
    conn = (virConnectPtr) PyvirConnect_Get(pyobj_conn);
LIBVIRT_BEGIN_ALLOW_THREADS;

    c_retval = virConnectNumOfDefinedNetworks(conn);
LIBVIRT_END_ALLOW_THREADS;
    py_retval = libvirt_intWrap((int) c_retval);
    return(py_retval);
}

PyObject *
libvirt_virConnectNumOfDomains(PyObject *self ATTRIBUTE_UNUSED, PyObject *args) {
    PyObject *py_retval;
    int c_retval;
    virConnectPtr conn;
    PyObject *pyobj_conn;

    if (!PyArg_ParseTuple(args, (char *)"O:virConnectNumOfDomains", &pyobj_conn))
        return(NULL);
    conn = (virConnectPtr) PyvirConnect_Get(pyobj_conn);
LIBVIRT_BEGIN_ALLOW_THREADS;

    c_retval = virConnectNumOfDomains(conn);
LIBVIRT_END_ALLOW_THREADS;
    py_retval = libvirt_intWrap((int) c_retval);
    return(py_retval);
}

PyObject *
libvirt_virDomainSetAutostart(PyObject *self ATTRIBUTE_UNUSED, PyObject *args) {
    PyObject *py_retval;
    int c_retval;
    virDomainPtr domain;
    PyObject *pyobj_domain;
    int autostart;

    if (!PyArg_ParseTuple(args, (char *)"Oi:virDomainSetAutostart", &pyobj_domain, &autostart))
        return(NULL);
    domain = (virDomainPtr) PyvirDomain_Get(pyobj_domain);
LIBVIRT_BEGIN_ALLOW_THREADS;

    c_retval = virDomainSetAutostart(domain, autostart);
LIBVIRT_END_ALLOW_THREADS;
    py_retval = libvirt_intWrap((int) c_retval);
    return(py_retval);
}

PyObject *
libvirt_virDomainCreateLinux(PyObject *self ATTRIBUTE_UNUSED, PyObject *args) {
    PyObject *py_retval;
    virDomainPtr c_retval;
    virConnectPtr conn;
    PyObject *pyobj_conn;
    char * xmlDesc;
    unsigned int flags;

    if (!PyArg_ParseTuple(args, (char *)"Ozi:virDomainCreateLinux", &pyobj_conn, &xmlDesc, &flags))
        return(NULL);
    conn = (virConnectPtr) PyvirConnect_Get(pyobj_conn);
LIBVIRT_BEGIN_ALLOW_THREADS;

    c_retval = virDomainCreateLinux(conn, xmlDesc, flags);
LIBVIRT_END_ALLOW_THREADS;
    py_retval = libvirt_virDomainPtrWrap((virDomainPtr) c_retval);
    return(py_retval);
}

PyObject *
libvirt_virDomainSetMaxMemory(PyObject *self ATTRIBUTE_UNUSED, PyObject *args) {
    PyObject *py_retval;
    int c_retval;
    virDomainPtr domain;
    PyObject *pyobj_domain;
    unsigned long memory;

    if (!PyArg_ParseTuple(args, (char *)"Ol:virDomainSetMaxMemory", &pyobj_domain, &memory))
        return(NULL);
    domain = (virDomainPtr) PyvirDomain_Get(pyobj_domain);
LIBVIRT_BEGIN_ALLOW_THREADS;

    c_retval = virDomainSetMaxMemory(domain, memory);
LIBVIRT_END_ALLOW_THREADS;
    py_retval = libvirt_intWrap((int) c_retval);
    return(py_retval);
}

PyObject *
libvirt_virInitialize(PyObject *self ATTRIBUTE_UNUSED, PyObject *args ATTRIBUTE_UNUSED) {
    PyObject *py_retval;
    int c_retval;
LIBVIRT_BEGIN_ALLOW_THREADS;

    c_retval = virInitialize();
LIBVIRT_END_ALLOW_THREADS;
    py_retval = libvirt_intWrap((int) c_retval);
    return(py_retval);
}

PyObject *
libvirt_virDomainGetConnect(PyObject *self ATTRIBUTE_UNUSED, PyObject *args) {
    PyObject *py_retval;
    virConnectPtr c_retval;
    virDomainPtr dom;
    PyObject *pyobj_dom;

    if (!PyArg_ParseTuple(args, (char *)"O:virDomainGetConnect", &pyobj_dom))
        return(NULL);
    dom = (virDomainPtr) PyvirDomain_Get(pyobj_dom);
LIBVIRT_BEGIN_ALLOW_THREADS;

    c_retval = virDomainGetConnect(dom);
LIBVIRT_END_ALLOW_THREADS;
    py_retval = libvirt_virConnectPtrWrap((virConnectPtr) c_retval);
    return(py_retval);
}

PyObject *
libvirt_virDomainSuspend(PyObject *self ATTRIBUTE_UNUSED, PyObject *args) {
    PyObject *py_retval;
    int c_retval;
    virDomainPtr domain;
    PyObject *pyobj_domain;

    if (!PyArg_ParseTuple(args, (char *)"O:virDomainSuspend", &pyobj_domain))
        return(NULL);
    domain = (virDomainPtr) PyvirDomain_Get(pyobj_domain);
LIBVIRT_BEGIN_ALLOW_THREADS;

    c_retval = virDomainSuspend(domain);
LIBVIRT_END_ALLOW_THREADS;
    py_retval = libvirt_intWrap((int) c_retval);
    return(py_retval);
}

PyObject *
libvirt_virNetworkCreate(PyObject *self ATTRIBUTE_UNUSED, PyObject *args) {
    PyObject *py_retval;
    int c_retval;
    virNetworkPtr network;
    PyObject *pyobj_network;

    if (!PyArg_ParseTuple(args, (char *)"O:virNetworkCreate", &pyobj_network))
        return(NULL);
    network = (virNetworkPtr) PyvirNetwork_Get(pyobj_network);
LIBVIRT_BEGIN_ALLOW_THREADS;

    c_retval = virNetworkCreate(network);
LIBVIRT_END_ALLOW_THREADS;
    py_retval = libvirt_intWrap((int) c_retval);
    return(py_retval);
}

PyObject *
libvirt_virDomainDestroy(PyObject *self ATTRIBUTE_UNUSED, PyObject *args) {
    PyObject *py_retval;
    int c_retval;
    virDomainPtr domain;
    PyObject *pyobj_domain;

    if (!PyArg_ParseTuple(args, (char *)"O:virDomainDestroy", &pyobj_domain))
        return(NULL);
    domain = (virDomainPtr) PyvirDomain_Get(pyobj_domain);
LIBVIRT_BEGIN_ALLOW_THREADS;

    c_retval = virDomainDestroy(domain);
LIBVIRT_END_ALLOW_THREADS;
    py_retval = libvirt_intWrap((int) c_retval);
    return(py_retval);
}

PyObject *
libvirt_virConnectNumOfNetworks(PyObject *self ATTRIBUTE_UNUSED, PyObject *args) {
    PyObject *py_retval;
    int c_retval;
    virConnectPtr conn;
    PyObject *pyobj_conn;

    if (!PyArg_ParseTuple(args, (char *)"O:virConnectNumOfNetworks", &pyobj_conn))
        return(NULL);
    conn = (virConnectPtr) PyvirConnect_Get(pyobj_conn);
LIBVIRT_BEGIN_ALLOW_THREADS;

    c_retval = virConnectNumOfNetworks(conn);
LIBVIRT_END_ALLOW_THREADS;
    py_retval = libvirt_intWrap((int) c_retval);
    return(py_retval);
}

PyObject *
libvirt_virDomainGetXMLDesc(PyObject *self ATTRIBUTE_UNUSED, PyObject *args) {
    PyObject *py_retval;
    char * c_retval;
    virDomainPtr domain;
    PyObject *pyobj_domain;
    int flags;

    if (!PyArg_ParseTuple(args, (char *)"Oi:virDomainGetXMLDesc", &pyobj_domain, &flags))
        return(NULL);
    domain = (virDomainPtr) PyvirDomain_Get(pyobj_domain);
LIBVIRT_BEGIN_ALLOW_THREADS;

    c_retval = virDomainGetXMLDesc(domain, flags);
LIBVIRT_END_ALLOW_THREADS;
    py_retval = libvirt_charPtrWrap((char *) c_retval);
    return(py_retval);
}

PyObject *
libvirt_virNetworkDestroy(PyObject *self ATTRIBUTE_UNUSED, PyObject *args) {
    PyObject *py_retval;
    int c_retval;
    virNetworkPtr network;
    PyObject *pyobj_network;

    if (!PyArg_ParseTuple(args, (char *)"O:virNetworkDestroy", &pyobj_network))
        return(NULL);
    network = (virNetworkPtr) PyvirNetwork_Get(pyobj_network);
LIBVIRT_BEGIN_ALLOW_THREADS;

    c_retval = virNetworkDestroy(network);
LIBVIRT_END_ALLOW_THREADS;
    py_retval = libvirt_intWrap((int) c_retval);
    return(py_retval);
}

PyObject *
libvirt_virNetworkGetBridgeName(PyObject *self ATTRIBUTE_UNUSED, PyObject *args) {
    PyObject *py_retval;
    char * c_retval;
    virNetworkPtr network;
    PyObject *pyobj_network;

    if (!PyArg_ParseTuple(args, (char *)"O:virNetworkGetBridgeName", &pyobj_network))
        return(NULL);
    network = (virNetworkPtr) PyvirNetwork_Get(pyobj_network);
LIBVIRT_BEGIN_ALLOW_THREADS;

    c_retval = virNetworkGetBridgeName(network);
LIBVIRT_END_ALLOW_THREADS;
    py_retval = libvirt_charPtrWrap((char *) c_retval);
    return(py_retval);
}

PyObject *
libvirt_virConnectGetType(PyObject *self ATTRIBUTE_UNUSED, PyObject *args) {
    PyObject *py_retval;
    const char * c_retval;
    virConnectPtr conn;
    PyObject *pyobj_conn;

    if (!PyArg_ParseTuple(args, (char *)"O:virConnectGetType", &pyobj_conn))
        return(NULL);
    conn = (virConnectPtr) PyvirConnect_Get(pyobj_conn);
LIBVIRT_BEGIN_ALLOW_THREADS;

    c_retval = virConnectGetType(conn);
LIBVIRT_END_ALLOW_THREADS;
    py_retval = libvirt_charPtrConstWrap((const char *) c_retval);
    return(py_retval);
}

PyObject *
libvirt_virDomainSave(PyObject *self ATTRIBUTE_UNUSED, PyObject *args) {
    PyObject *py_retval;
    int c_retval;
    virDomainPtr domain;
    PyObject *pyobj_domain;
    char * to;

    if (!PyArg_ParseTuple(args, (char *)"Oz:virDomainSave", &pyobj_domain, &to))
        return(NULL);
    domain = (virDomainPtr) PyvirDomain_Get(pyobj_domain);
LIBVIRT_BEGIN_ALLOW_THREADS;

    c_retval = virDomainSave(domain, to);
LIBVIRT_END_ALLOW_THREADS;
    py_retval = libvirt_intWrap((int) c_retval);
    return(py_retval);
}

PyObject *
libvirt_virDomainCreate(PyObject *self ATTRIBUTE_UNUSED, PyObject *args) {
    PyObject *py_retval;
    int c_retval;
    virDomainPtr domain;
    PyObject *pyobj_domain;

    if (!PyArg_ParseTuple(args, (char *)"O:virDomainCreate", &pyobj_domain))
        return(NULL);
    domain = (virDomainPtr) PyvirDomain_Get(pyobj_domain);
LIBVIRT_BEGIN_ALLOW_THREADS;

    c_retval = virDomainCreate(domain);
LIBVIRT_END_ALLOW_THREADS;
    py_retval = libvirt_intWrap((int) c_retval);
    return(py_retval);
}

PyObject *
libvirt_virDomainCoreDump(PyObject *self ATTRIBUTE_UNUSED, PyObject *args) {
    PyObject *py_retval;
    int c_retval;
    virDomainPtr domain;
    PyObject *pyobj_domain;
    char * to;
    int flags;

    if (!PyArg_ParseTuple(args, (char *)"Ozi:virDomainCoreDump", &pyobj_domain, &to, &flags))
        return(NULL);
    domain = (virDomainPtr) PyvirDomain_Get(pyobj_domain);
LIBVIRT_BEGIN_ALLOW_THREADS;

    c_retval = virDomainCoreDump(domain, to, flags);
LIBVIRT_END_ALLOW_THREADS;
    py_retval = libvirt_intWrap((int) c_retval);
    return(py_retval);
}

PyObject *
libvirt_virDomainSetMemory(PyObject *self ATTRIBUTE_UNUSED, PyObject *args) {
    PyObject *py_retval;
    int c_retval;
    virDomainPtr domain;
    PyObject *pyobj_domain;
    unsigned long memory;

    if (!PyArg_ParseTuple(args, (char *)"Ol:virDomainSetMemory", &pyobj_domain, &memory))
        return(NULL);
    domain = (virDomainPtr) PyvirDomain_Get(pyobj_domain);
LIBVIRT_BEGIN_ALLOW_THREADS;

    c_retval = virDomainSetMemory(domain, memory);
LIBVIRT_END_ALLOW_THREADS;
    py_retval = libvirt_intWrap((int) c_retval);
    return(py_retval);
}

PyObject *
libvirt_virNetworkSetAutostart(PyObject *self ATTRIBUTE_UNUSED, PyObject *args) {
    PyObject *py_retval;
    int c_retval;
    virNetworkPtr network;
    PyObject *pyobj_network;
    int autostart;

    if (!PyArg_ParseTuple(args, (char *)"Oi:virNetworkSetAutostart", &pyobj_network, &autostart))
        return(NULL);
    network = (virNetworkPtr) PyvirNetwork_Get(pyobj_network);
LIBVIRT_BEGIN_ALLOW_THREADS;

    c_retval = virNetworkSetAutostart(network, autostart);
LIBVIRT_END_ALLOW_THREADS;
    py_retval = libvirt_intWrap((int) c_retval);
    return(py_retval);
}

PyObject *
libvirt_virDomainGetMaxMemory(PyObject *self ATTRIBUTE_UNUSED, PyObject *args) {
    PyObject *py_retval;
    unsigned long c_retval;
    virDomainPtr domain;
    PyObject *pyobj_domain;

    if (!PyArg_ParseTuple(args, (char *)"O:virDomainGetMaxMemory", &pyobj_domain))
        return(NULL);
    domain = (virDomainPtr) PyvirDomain_Get(pyobj_domain);
LIBVIRT_BEGIN_ALLOW_THREADS;

    c_retval = virDomainGetMaxMemory(domain);
LIBVIRT_END_ALLOW_THREADS;
    py_retval = libvirt_longWrap((long) c_retval);
    return(py_retval);
}

PyObject *
libvirt_virResetLastError(PyObject *self ATTRIBUTE_UNUSED, PyObject *args ATTRIBUTE_UNUSED) {
LIBVIRT_BEGIN_ALLOW_THREADS;

    virResetLastError();
LIBVIRT_END_ALLOW_THREADS;
    Py_INCREF(Py_None);
    return(Py_None);
}

PyObject *
libvirt_virNetworkDefineXML(PyObject *self ATTRIBUTE_UNUSED, PyObject *args) {
    PyObject *py_retval;
    virNetworkPtr c_retval;
    virConnectPtr conn;
    PyObject *pyobj_conn;
    char * xml;

    if (!PyArg_ParseTuple(args, (char *)"Oz:virNetworkDefineXML", &pyobj_conn, &xml))
        return(NULL);
    conn = (virConnectPtr) PyvirConnect_Get(pyobj_conn);
LIBVIRT_BEGIN_ALLOW_THREADS;

    c_retval = virNetworkDefineXML(conn, xml);
LIBVIRT_END_ALLOW_THREADS;
    py_retval = libvirt_virNetworkPtrWrap((virNetworkPtr) c_retval);
    return(py_retval);
}

PyObject *
libvirt_virConnResetLastError(PyObject *self ATTRIBUTE_UNUSED, PyObject *args) {
    virConnectPtr conn;
    PyObject *pyobj_conn;

    if (!PyArg_ParseTuple(args, (char *)"O:virConnResetLastError", &pyobj_conn))
        return(NULL);
    conn = (virConnectPtr) PyvirConnect_Get(pyobj_conn);
LIBVIRT_BEGIN_ALLOW_THREADS;

    virConnResetLastError(conn);
LIBVIRT_END_ALLOW_THREADS;
    Py_INCREF(Py_None);
    return(Py_None);
}

PyObject *
libvirt_virDomainResume(PyObject *self ATTRIBUTE_UNUSED, PyObject *args) {
    PyObject *py_retval;
    int c_retval;
    virDomainPtr domain;
    PyObject *pyobj_domain;

    if (!PyArg_ParseTuple(args, (char *)"O:virDomainResume", &pyobj_domain))
        return(NULL);
    domain = (virDomainPtr) PyvirDomain_Get(pyobj_domain);
LIBVIRT_BEGIN_ALLOW_THREADS;

    c_retval = virDomainResume(domain);
LIBVIRT_END_ALLOW_THREADS;
    py_retval = libvirt_intWrap((int) c_retval);
    return(py_retval);
}

PyObject *
libvirt_virConnectGetHostname(PyObject *self ATTRIBUTE_UNUSED, PyObject *args) {
    PyObject *py_retval;
    char * c_retval;
    virConnectPtr conn;
    PyObject *pyobj_conn;

    if (!PyArg_ParseTuple(args, (char *)"O:virConnectGetHostname", &pyobj_conn))
        return(NULL);
    conn = (virConnectPtr) PyvirConnect_Get(pyobj_conn);
LIBVIRT_BEGIN_ALLOW_THREADS;

    c_retval = virConnectGetHostname(conn);
LIBVIRT_END_ALLOW_THREADS;
    py_retval = libvirt_charPtrWrap((char *) c_retval);
    return(py_retval);
}

PyObject *
libvirt_virDomainGetName(PyObject *self ATTRIBUTE_UNUSED, PyObject *args) {
    PyObject *py_retval;
    const char * c_retval;
    virDomainPtr domain;
    PyObject *pyobj_domain;

    if (!PyArg_ParseTuple(args, (char *)"O:virDomainGetName", &pyobj_domain))
        return(NULL);
    domain = (virDomainPtr) PyvirDomain_Get(pyobj_domain);
LIBVIRT_BEGIN_ALLOW_THREADS;

    c_retval = virDomainGetName(domain);
LIBVIRT_END_ALLOW_THREADS;
    py_retval = libvirt_charPtrConstWrap((const char *) c_retval);
    return(py_retval);
}

PyObject *
libvirt_virNetworkGetXMLDesc(PyObject *self ATTRIBUTE_UNUSED, PyObject *args) {
    PyObject *py_retval;
    char * c_retval;
    virNetworkPtr network;
    PyObject *pyobj_network;
    int flags;

    if (!PyArg_ParseTuple(args, (char *)"Oi:virNetworkGetXMLDesc", &pyobj_network, &flags))
        return(NULL);
    network = (virNetworkPtr) PyvirNetwork_Get(pyobj_network);
LIBVIRT_BEGIN_ALLOW_THREADS;

    c_retval = virNetworkGetXMLDesc(network, flags);
LIBVIRT_END_ALLOW_THREADS;
    py_retval = libvirt_charPtrWrap((char *) c_retval);
    return(py_retval);
}

PyObject *
libvirt_virNetworkGetName(PyObject *self ATTRIBUTE_UNUSED, PyObject *args) {
    PyObject *py_retval;
    const char * c_retval;
    virNetworkPtr network;
    PyObject *pyobj_network;

    if (!PyArg_ParseTuple(args, (char *)"O:virNetworkGetName", &pyobj_network))
        return(NULL);
    network = (virNetworkPtr) PyvirNetwork_Get(pyobj_network);
LIBVIRT_BEGIN_ALLOW_THREADS;

    c_retval = virNetworkGetName(network);
LIBVIRT_END_ALLOW_THREADS;
    py_retval = libvirt_charPtrConstWrap((const char *) c_retval);
    return(py_retval);
}

PyObject *
libvirt_virConnectGetCapabilities(PyObject *self ATTRIBUTE_UNUSED, PyObject *args) {
    PyObject *py_retval;
    char * c_retval;
    virConnectPtr conn;
    PyObject *pyobj_conn;

    if (!PyArg_ParseTuple(args, (char *)"O:virConnectGetCapabilities", &pyobj_conn))
        return(NULL);
    conn = (virConnectPtr) PyvirConnect_Get(pyobj_conn);
LIBVIRT_BEGIN_ALLOW_THREADS;

    c_retval = virConnectGetCapabilities(conn);
LIBVIRT_END_ALLOW_THREADS;
    py_retval = libvirt_charPtrWrap((char *) c_retval);
    return(py_retval);
}

PyObject *
libvirt_virDomainLookupByName(PyObject *self ATTRIBUTE_UNUSED, PyObject *args) {
    PyObject *py_retval;
    virDomainPtr c_retval;
    virConnectPtr conn;
    PyObject *pyobj_conn;
    char * name;

    if (!PyArg_ParseTuple(args, (char *)"Oz:virDomainLookupByName", &pyobj_conn, &name))
        return(NULL);
    conn = (virConnectPtr) PyvirConnect_Get(pyobj_conn);
LIBVIRT_BEGIN_ALLOW_THREADS;

    c_retval = virDomainLookupByName(conn, name);
LIBVIRT_END_ALLOW_THREADS;
    py_retval = libvirt_virDomainPtrWrap((virDomainPtr) c_retval);
    return(py_retval);
}

PyObject *
libvirt_virDomainPinVcpu(PyObject *self ATTRIBUTE_UNUSED, PyObject *args) {
    PyObject *py_retval;
    int c_retval;
    virDomainPtr domain;
    PyObject *pyobj_domain;
    unsigned int vcpu;
    unsigned char * cpumap;
    int maplen;

    if (!PyArg_ParseTuple(args, (char *)"Oizi:virDomainPinVcpu", &pyobj_domain, &vcpu, &cpumap, &maplen))
        return(NULL);
    domain = (virDomainPtr) PyvirDomain_Get(pyobj_domain);
LIBVIRT_BEGIN_ALLOW_THREADS;

    c_retval = virDomainPinVcpu(domain, vcpu, cpumap, maplen);
LIBVIRT_END_ALLOW_THREADS;
    py_retval = libvirt_intWrap((int) c_retval);
    return(py_retval);
}

PyObject *
libvirt_virDomainRestore(PyObject *self ATTRIBUTE_UNUSED, PyObject *args) {
    PyObject *py_retval;
    int c_retval;
    virConnectPtr conn;
    PyObject *pyobj_conn;
    char * frm;

    if (!PyArg_ParseTuple(args, (char *)"Oz:virDomainRestore", &pyobj_conn, &frm))
        return(NULL);
    conn = (virConnectPtr) PyvirConnect_Get(pyobj_conn);
LIBVIRT_BEGIN_ALLOW_THREADS;

    c_retval = virDomainRestore(conn, frm);
LIBVIRT_END_ALLOW_THREADS;
    py_retval = libvirt_intWrap((int) c_retval);
    return(py_retval);
}

PyObject *
libvirt_virNetworkLookupByUUIDString(PyObject *self ATTRIBUTE_UNUSED, PyObject *args) {
    PyObject *py_retval;
    virNetworkPtr c_retval;
    virConnectPtr conn;
    PyObject *pyobj_conn;
    char * uuidstr;

    if (!PyArg_ParseTuple(args, (char *)"Oz:virNetworkLookupByUUIDString", &pyobj_conn, &uuidstr))
        return(NULL);
    conn = (virConnectPtr) PyvirConnect_Get(pyobj_conn);
LIBVIRT_BEGIN_ALLOW_THREADS;

    c_retval = virNetworkLookupByUUIDString(conn, uuidstr);
LIBVIRT_END_ALLOW_THREADS;
    py_retval = libvirt_virNetworkPtrWrap((virNetworkPtr) c_retval);
    return(py_retval);
}

PyObject *
libvirt_virDomainLookupByID(PyObject *self ATTRIBUTE_UNUSED, PyObject *args) {
    PyObject *py_retval;
    virDomainPtr c_retval;
    virConnectPtr conn;
    PyObject *pyobj_conn;
    int id;

    if (!PyArg_ParseTuple(args, (char *)"Oi:virDomainLookupByID", &pyobj_conn, &id))
        return(NULL);
    conn = (virConnectPtr) PyvirConnect_Get(pyobj_conn);
LIBVIRT_BEGIN_ALLOW_THREADS;

    c_retval = virDomainLookupByID(conn, id);
LIBVIRT_END_ALLOW_THREADS;
    py_retval = libvirt_virDomainPtrWrap((virDomainPtr) c_retval);
    return(py_retval);
}

PyObject *
libvirt_virNetworkCreateXML(PyObject *self ATTRIBUTE_UNUSED, PyObject *args) {
    PyObject *py_retval;
    virNetworkPtr c_retval;
    virConnectPtr conn;
    PyObject *pyobj_conn;
    char * xmlDesc;

    if (!PyArg_ParseTuple(args, (char *)"Oz:virNetworkCreateXML", &pyobj_conn, &xmlDesc))
        return(NULL);
    conn = (virConnectPtr) PyvirConnect_Get(pyobj_conn);
LIBVIRT_BEGIN_ALLOW_THREADS;

    c_retval = virNetworkCreateXML(conn, xmlDesc);
LIBVIRT_END_ALLOW_THREADS;
    py_retval = libvirt_virNetworkPtrWrap((virNetworkPtr) c_retval);
    return(py_retval);
}

PyObject *
libvirt_virConnectNumOfDefinedDomains(PyObject *self ATTRIBUTE_UNUSED, PyObject *args) {
    PyObject *py_retval;
    int c_retval;
    virConnectPtr conn;
    PyObject *pyobj_conn;

    if (!PyArg_ParseTuple(args, (char *)"O:virConnectNumOfDefinedDomains", &pyobj_conn))
        return(NULL);
    conn = (virConnectPtr) PyvirConnect_Get(pyobj_conn);
LIBVIRT_BEGIN_ALLOW_THREADS;

    c_retval = virConnectNumOfDefinedDomains(conn);
LIBVIRT_END_ALLOW_THREADS;
    py_retval = libvirt_intWrap((int) c_retval);
    return(py_retval);
}

PyObject *
libvirt_virDomainUndefine(PyObject *self ATTRIBUTE_UNUSED, PyObject *args) {
    PyObject *py_retval;
    int c_retval;
    virDomainPtr domain;
    PyObject *pyobj_domain;

    if (!PyArg_ParseTuple(args, (char *)"O:virDomainUndefine", &pyobj_domain))
        return(NULL);
    domain = (virDomainPtr) PyvirDomain_Get(pyobj_domain);
LIBVIRT_BEGIN_ALLOW_THREADS;

    c_retval = virDomainUndefine(domain);
LIBVIRT_END_ALLOW_THREADS;
    py_retval = libvirt_intWrap((int) c_retval);
    return(py_retval);
}

PyObject *
libvirt_virDomainReboot(PyObject *self ATTRIBUTE_UNUSED, PyObject *args) {
    PyObject *py_retval;
    int c_retval;
    virDomainPtr domain;
    PyObject *pyobj_domain;
    unsigned int flags;

    if (!PyArg_ParseTuple(args, (char *)"Oi:virDomainReboot", &pyobj_domain, &flags))
        return(NULL);
    domain = (virDomainPtr) PyvirDomain_Get(pyobj_domain);
LIBVIRT_BEGIN_ALLOW_THREADS;

    c_retval = virDomainReboot(domain, flags);
LIBVIRT_END_ALLOW_THREADS;
    py_retval = libvirt_intWrap((int) c_retval);
    return(py_retval);
}

PyObject *
libvirt_virNetworkGetUUIDString(PyObject *self ATTRIBUTE_UNUSED, PyObject *args) {
    PyObject *py_retval;
    int c_retval;
    virNetworkPtr network;
    PyObject *pyobj_network;
    char * buf;

    if (!PyArg_ParseTuple(args, (char *)"Oz:virNetworkGetUUIDString", &pyobj_network, &buf))
        return(NULL);
    network = (virNetworkPtr) PyvirNetwork_Get(pyobj_network);
LIBVIRT_BEGIN_ALLOW_THREADS;

    c_retval = virNetworkGetUUIDString(network, buf);
LIBVIRT_END_ALLOW_THREADS;
    py_retval = libvirt_intWrap((int) c_retval);
    return(py_retval);
}

PyObject *
libvirt_virNetworkLookupByName(PyObject *self ATTRIBUTE_UNUSED, PyObject *args) {
    PyObject *py_retval;
    virNetworkPtr c_retval;
    virConnectPtr conn;
    PyObject *pyobj_conn;
    char * name;

    if (!PyArg_ParseTuple(args, (char *)"Oz:virNetworkLookupByName", &pyobj_conn, &name))
        return(NULL);
    conn = (virConnectPtr) PyvirConnect_Get(pyobj_conn);
LIBVIRT_BEGIN_ALLOW_THREADS;

    c_retval = virNetworkLookupByName(conn, name);
LIBVIRT_END_ALLOW_THREADS;
    py_retval = libvirt_virNetworkPtrWrap((virNetworkPtr) c_retval);
    return(py_retval);
}

PyObject *
libvirt_virDomainGetMaxVcpus(PyObject *self ATTRIBUTE_UNUSED, PyObject *args) {
    PyObject *py_retval;
    int c_retval;
    virDomainPtr domain;
    PyObject *pyobj_domain;

    if (!PyArg_ParseTuple(args, (char *)"O:virDomainGetMaxVcpus", &pyobj_domain))
        return(NULL);
    domain = (virDomainPtr) PyvirDomain_Get(pyobj_domain);
LIBVIRT_BEGIN_ALLOW_THREADS;

    c_retval = virDomainGetMaxVcpus(domain);
LIBVIRT_END_ALLOW_THREADS;
    py_retval = libvirt_intWrap((int) c_retval);
    return(py_retval);
}

PyObject *
libvirt_virDomainDetachDevice(PyObject *self ATTRIBUTE_UNUSED, PyObject *args) {
    PyObject *py_retval;
    int c_retval;
    virDomainPtr domain;
    PyObject *pyobj_domain;
    char * xml;

    if (!PyArg_ParseTuple(args, (char *)"Oz:virDomainDetachDevice", &pyobj_domain, &xml))
        return(NULL);
    domain = (virDomainPtr) PyvirDomain_Get(pyobj_domain);
LIBVIRT_BEGIN_ALLOW_THREADS;

    c_retval = virDomainDetachDevice(domain, xml);
LIBVIRT_END_ALLOW_THREADS;
    py_retval = libvirt_intWrap((int) c_retval);
    return(py_retval);
}

PyObject *
libvirt_virDomainAttachDevice(PyObject *self ATTRIBUTE_UNUSED, PyObject *args) {
    PyObject *py_retval;
    int c_retval;
    virDomainPtr domain;
    PyObject *pyobj_domain;
    char * xml;

    if (!PyArg_ParseTuple(args, (char *)"Oz:virDomainAttachDevice", &pyobj_domain, &xml))
        return(NULL);
    domain = (virDomainPtr) PyvirDomain_Get(pyobj_domain);
LIBVIRT_BEGIN_ALLOW_THREADS;

    c_retval = virDomainAttachDevice(domain, xml);
LIBVIRT_END_ALLOW_THREADS;
    py_retval = libvirt_intWrap((int) c_retval);
    return(py_retval);
}

PyObject *
libvirt_virConnectGetURI(PyObject *self ATTRIBUTE_UNUSED, PyObject *args) {
    PyObject *py_retval;
    char * c_retval;
    virConnectPtr conn;
    PyObject *pyobj_conn;

    if (!PyArg_ParseTuple(args, (char *)"O:virConnectGetURI", &pyobj_conn))
        return(NULL);
    conn = (virConnectPtr) PyvirConnect_Get(pyobj_conn);
LIBVIRT_BEGIN_ALLOW_THREADS;

    c_retval = virConnectGetURI(conn);
LIBVIRT_END_ALLOW_THREADS;
    py_retval = libvirt_charPtrWrap((char *) c_retval);
    return(py_retval);
}

PyObject *
libvirt_virConnectOpenReadOnly(PyObject *self ATTRIBUTE_UNUSED, PyObject *args) {
    PyObject *py_retval;
    virConnectPtr c_retval;
    char * name;

    if (!PyArg_ParseTuple(args, (char *)"z:virConnectOpenReadOnly", &name))
        return(NULL);
LIBVIRT_BEGIN_ALLOW_THREADS;

    c_retval = virConnectOpenReadOnly(name);
LIBVIRT_END_ALLOW_THREADS;
    py_retval = libvirt_virConnectPtrWrap((virConnectPtr) c_retval);
    return(py_retval);
}

PyObject *
libvirt_virNetworkUndefine(PyObject *self ATTRIBUTE_UNUSED, PyObject *args) {
    PyObject *py_retval;
    int c_retval;
    virNetworkPtr network;
    PyObject *pyobj_network;

    if (!PyArg_ParseTuple(args, (char *)"O:virNetworkUndefine", &pyobj_network))
        return(NULL);
    network = (virNetworkPtr) PyvirNetwork_Get(pyobj_network);
LIBVIRT_BEGIN_ALLOW_THREADS;

    c_retval = virNetworkUndefine(network);
LIBVIRT_END_ALLOW_THREADS;
    py_retval = libvirt_intWrap((int) c_retval);
    return(py_retval);
}

PyObject *
libvirt_virNetworkGetConnect(PyObject *self ATTRIBUTE_UNUSED, PyObject *args) {
    PyObject *py_retval;
    virConnectPtr c_retval;
    virNetworkPtr net;
    PyObject *pyobj_net;

    if (!PyArg_ParseTuple(args, (char *)"O:virNetworkGetConnect", &pyobj_net))
        return(NULL);
    net = (virNetworkPtr) PyvirNetwork_Get(pyobj_net);
LIBVIRT_BEGIN_ALLOW_THREADS;

    c_retval = virNetworkGetConnect(net);
LIBVIRT_END_ALLOW_THREADS;
    py_retval = libvirt_virConnectPtrWrap((virConnectPtr) c_retval);
    return(py_retval);
}

PyObject *
libvirt_virDomainGetOSType(PyObject *self ATTRIBUTE_UNUSED, PyObject *args) {
    PyObject *py_retval;
    char * c_retval;
    virDomainPtr domain;
    PyObject *pyobj_domain;

    if (!PyArg_ParseTuple(args, (char *)"O:virDomainGetOSType", &pyobj_domain))
        return(NULL);
    domain = (virDomainPtr) PyvirDomain_Get(pyobj_domain);
LIBVIRT_BEGIN_ALLOW_THREADS;

    c_retval = virDomainGetOSType(domain);
LIBVIRT_END_ALLOW_THREADS;
    py_retval = libvirt_charPtrWrap((char *) c_retval);
    return(py_retval);
}

PyObject *
libvirt_virConnectGetMaxVcpus(PyObject *self ATTRIBUTE_UNUSED, PyObject *args) {
    PyObject *py_retval;
    int c_retval;
    virConnectPtr conn;
    PyObject *pyobj_conn;
    char * type;

    if (!PyArg_ParseTuple(args, (char *)"Oz:virConnectGetMaxVcpus", &pyobj_conn, &type))
        return(NULL);
    conn = (virConnectPtr) PyvirConnect_Get(pyobj_conn);
LIBVIRT_BEGIN_ALLOW_THREADS;

    c_retval = virConnectGetMaxVcpus(conn, type);
LIBVIRT_END_ALLOW_THREADS;
    py_retval = libvirt_intWrap((int) c_retval);
    return(py_retval);
}

PyObject *
libvirt_virDomainGetUUIDString(PyObject *self ATTRIBUTE_UNUSED, PyObject *args) {
    PyObject *py_retval;
    int c_retval;
    virDomainPtr domain;
    PyObject *pyobj_domain;
    char * buf;

    if (!PyArg_ParseTuple(args, (char *)"Oz:virDomainGetUUIDString", &pyobj_domain, &buf))
        return(NULL);
    domain = (virDomainPtr) PyvirDomain_Get(pyobj_domain);
LIBVIRT_BEGIN_ALLOW_THREADS;

    c_retval = virDomainGetUUIDString(domain, buf);
LIBVIRT_END_ALLOW_THREADS;
    py_retval = libvirt_intWrap((int) c_retval);
    return(py_retval);
}

PyObject *
libvirt_virDomainMigrate(PyObject *self ATTRIBUTE_UNUSED, PyObject *args) {
    PyObject *py_retval;
    virDomainPtr c_retval;
    virDomainPtr domain;
    PyObject *pyobj_domain;
    virConnectPtr dconn;
    PyObject *pyobj_dconn;
    unsigned long flags;
    char * dname;
    char * uri;
    unsigned long bandwidth;

    if (!PyArg_ParseTuple(args, (char *)"OOlzzl:virDomainMigrate", &pyobj_domain, &pyobj_dconn, &flags, &dname, &uri, &bandwidth))
        return(NULL);
    domain = (virDomainPtr) PyvirDomain_Get(pyobj_domain);
    dconn = (virConnectPtr) PyvirConnect_Get(pyobj_dconn);
LIBVIRT_BEGIN_ALLOW_THREADS;

    c_retval = virDomainMigrate(domain, dconn, flags, dname, uri, bandwidth);
LIBVIRT_END_ALLOW_THREADS;
    py_retval = libvirt_virDomainPtrWrap((virDomainPtr) c_retval);
    return(py_retval);
}

PyObject *
libvirt_virConnectOpen(PyObject *self ATTRIBUTE_UNUSED, PyObject *args) {
    PyObject *py_retval;
    virConnectPtr c_retval;
    char * name;

    if (!PyArg_ParseTuple(args, (char *)"z:virConnectOpen", &name))
        return(NULL);
LIBVIRT_BEGIN_ALLOW_THREADS;

    c_retval = virConnectOpen(name);
LIBVIRT_END_ALLOW_THREADS;
    py_retval = libvirt_virConnectPtrWrap((virConnectPtr) c_retval);
    return(py_retval);
}

PyObject *
libvirt_virDomainSetVcpus(PyObject *self ATTRIBUTE_UNUSED, PyObject *args) {
    PyObject *py_retval;
    int c_retval;
    virDomainPtr domain;
    PyObject *pyobj_domain;
    unsigned int nvcpus;

    if (!PyArg_ParseTuple(args, (char *)"Oi:virDomainSetVcpus", &pyobj_domain, &nvcpus))
        return(NULL);
    domain = (virDomainPtr) PyvirDomain_Get(pyobj_domain);
LIBVIRT_BEGIN_ALLOW_THREADS;

    c_retval = virDomainSetVcpus(domain, nvcpus);
LIBVIRT_END_ALLOW_THREADS;
    py_retval = libvirt_intWrap((int) c_retval);
    return(py_retval);
}

PyObject *
libvirt_virDomainGetID(PyObject *self ATTRIBUTE_UNUSED, PyObject *args) {
    PyObject *py_retval;
    unsigned int c_retval;
    virDomainPtr domain;
    PyObject *pyobj_domain;

    if (!PyArg_ParseTuple(args, (char *)"O:virDomainGetID", &pyobj_domain))
        return(NULL);
    domain = (virDomainPtr) PyvirDomain_Get(pyobj_domain);
LIBVIRT_BEGIN_ALLOW_THREADS;

    c_retval = virDomainGetID(domain);
LIBVIRT_END_ALLOW_THREADS;
    py_retval = libvirt_intWrap((int) c_retval);
    return(py_retval);
}

