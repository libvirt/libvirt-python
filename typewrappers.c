/*
 * types.c: converter functions between the internal representation
 *          and the Python objects
 *
 * Copyright (C) 2005-2019 Red Hat, Inc.
 *
 * Daniel Veillard <veillard@redhat.com>
 */

/* Horrible kludge to work around even more horrible name-space pollution
 * via Python.h.  That file includes /usr/include/python3.x/pyconfig*.h,
 * which has over 180 autoconf-style HAVE_* definitions.  Shame on them.  */
#undef HAVE_PTHREAD_H

#include "typewrappers.h"
#include "libvirt-utils.h"

static PyObject *
libvirt_buildPyObject(void *cobj,
                      const char *name,
                      PyCapsule_Destructor destr)
{
    return PyCapsule_New(cobj, name, destr);
}

PyObject *
libvirt_intWrap(int val)
{
    return PyLong_FromLong((long) val);
}

PyObject *
libvirt_uintWrap(uint val)
{
    return PyLong_FromLong((long) val);
}

PyObject *
libvirt_longWrap(long val)
{
    return PyLong_FromLong(val);
}

PyObject *
libvirt_ulongWrap(unsigned long val)
{
    return PyLong_FromLong(val);
}

PyObject *
libvirt_longlongWrap(long long val)
{
    return PyLong_FromLongLong(val);
}

PyObject *
libvirt_ulonglongWrap(unsigned long long val)
{
    return PyLong_FromUnsignedLongLong(val);
}

PyObject *
libvirt_charPtrSizeWrap(char *str, Py_ssize_t size)
{
    if (str == NULL) {
        return VIR_PY_NONE;
    }
    return PyBytes_FromStringAndSize(str, size);
}

PyObject *
libvirt_charPtrWrap(char *str)
{
    if (str == NULL) {
        return VIR_PY_NONE;
    }
    return PyUnicode_FromString(str);
}

PyObject *
libvirt_constcharPtrWrap(const char *str)
{
    if (str == NULL) {
        return VIR_PY_NONE;
    }
    return PyUnicode_FromString(str);
}

PyObject *
libvirt_boolWrap(int val)
{
    if (val)
        Py_RETURN_TRUE;
    else
        Py_RETURN_FALSE;
}

int
libvirt_intUnwrap(PyObject *obj,
                  int *val)
{
    long long_val;

    if (!obj) {
        PyErr_SetString(PyExc_TypeError, "unexpected type");
        return -1;
    }

    /* If obj is type of PyInt_Type, PyInt_AsLong converts it
     * to C long type directly. If it is of PyLong_Type, PyInt_AsLong
     * will call PyLong_AsLong() to deal with it automatically.
     */
    long_val = PyLong_AsLong(obj);
    if ((long_val == -1) && PyErr_Occurred())
        return -1;

#if LONG_MAX != INT_MAX
    if (long_val >= INT_MIN && long_val <= INT_MAX) {
        *val = long_val;
    } else {
        PyErr_SetString(PyExc_OverflowError,
                        "Python int too large to convert to C int");
        return -1;
    }
#else
    *val = long_val;
#endif
    return 0;
}

int
libvirt_uintUnwrap(PyObject *obj,
                   unsigned int *val)
{
    long long_val;

    if (!obj) {
        PyErr_SetString(PyExc_TypeError, "unexpected type");
        return -1;
    }

    long_val = PyLong_AsLong(obj);
    if ((long_val == -1) && PyErr_Occurred())
        return -1;

    if (long_val >= 0 && long_val <= UINT_MAX) {
        *val = long_val;
    } else {
        PyErr_SetString(PyExc_OverflowError,
                        "Python int too large to convert to C unsigned int");
        return -1;
    }
    return 0;
}

int
libvirt_longUnwrap(PyObject *obj,
                   long *val)
{
    long long_val;

    if (!obj) {
        PyErr_SetString(PyExc_TypeError, "unexpected type");
        return -1;
    }

    long_val = PyLong_AsLong(obj);
    if ((long_val == -1) && PyErr_Occurred())
        return -1;

    *val = long_val;
    return 0;
}

int
libvirt_ulongUnwrap(PyObject *obj,
                    unsigned long *val)
{
    long long_val;

    if (!obj) {
        PyErr_SetString(PyExc_TypeError, "unexpected type");
        return -1;
    }

    long_val = PyLong_AsLong(obj);
    if ((long_val == -1) && PyErr_Occurred())
        return -1;

    if (long_val >= 0) {
        *val = long_val;
    } else {
        PyErr_SetString(PyExc_OverflowError,
                        "negative Python int cannot be converted to C unsigned long");
        return -1;
    }
    return 0;
}

int
libvirt_longlongUnwrap(PyObject *obj,
                       long long *val)
{
    long long llong_val = -1;

    if (!obj) {
        PyErr_SetString(PyExc_TypeError, "unexpected type");
        return -1;
    }

    if (PyLong_Check(obj))
        llong_val = PyLong_AsLongLong(obj);
    else
        PyErr_SetString(PyExc_TypeError, "an integer is required");

    if ((llong_val == -1) && PyErr_Occurred())
        return -1;

    *val = llong_val;
    return 0;
}

int
libvirt_ulonglongUnwrap(PyObject *obj,
                        unsigned long long *val)
{
    unsigned long long ullong_val = -1;

    if (!obj) {
        PyErr_SetString(PyExc_TypeError, "unexpected type");
        return -1;
    }

    if (PyLong_Check(obj)) {
        ullong_val = PyLong_AsUnsignedLongLong(obj);
    } else {
        PyErr_SetString(PyExc_TypeError, "an integer is required");
    }

    if ((ullong_val == (unsigned long long)-1) && PyErr_Occurred())
        return -1;

    *val = ullong_val;
    return 0;
}

int
libvirt_doubleUnwrap(PyObject *obj,
                     double *val)
{
    double double_val;

    if (!obj) {
        PyErr_SetString(PyExc_TypeError, "unexpected type");
        return -1;
    }

    double_val = PyFloat_AsDouble(obj);
    if ((double_val == -1) && PyErr_Occurred())
        return -1;

    *val = double_val;
    return 0;
}

int
libvirt_boolUnwrap(PyObject *obj,
                   bool *val)
{
    int ret;

    if (!obj) {
        PyErr_SetString(PyExc_TypeError, "unexpected type");
        return -1;
    }

    if ((ret = PyObject_IsTrue(obj)) < 0)
        return ret;

    *val = ret > 0;
    return 0;
}

int
libvirt_charPtrUnwrap(PyObject *obj,
                      char **str)
{
    PyObject *bytes;
    const char *ret;
    *str = NULL;
    if (!obj) {
        PyErr_SetString(PyExc_TypeError, "unexpected type");
        return -1;
    }

    if (!(bytes = PyUnicode_AsUTF8String(obj)))
        return -1;
    ret = PyBytes_AsString(bytes);
    if (ret) {
        *str = strdup(ret);
        if (!*str)
            PyErr_NoMemory();
    }
    Py_DECREF(bytes);
    return ret && *str ? 0 : -1;
}

int
libvirt_charPtrSizeUnwrap(PyObject *obj,
                          char **str,
                          Py_ssize_t *size)
{
    *str = NULL;
    *size = 0;
    if (!obj) {
        PyErr_SetString(PyExc_TypeError, "unexpected type");
        return -1;
    }

    return PyBytes_AsStringAndSize(obj, str, size);
}

PyObject *
libvirt_virDomainPtrWrap(virDomainPtr node)
{
    PyObject *ret;

    if (node == NULL) {
        return VIR_PY_NONE;
    }

    ret = libvirt_buildPyObject(node, "virDomainPtr", NULL);
    return ret;
}

PyObject *
libvirt_virNetworkPtrWrap(virNetworkPtr node)
{
    PyObject *ret;

    if (node == NULL) {
        return VIR_PY_NONE;
    }

    ret = libvirt_buildPyObject(node, "virNetworkPtr", NULL);
    return ret;
}

PyObject *
libvirt_virNetworkPortPtrWrap(virNetworkPortPtr node)
{
    PyObject *ret;

    if (node == NULL) {
        return VIR_PY_NONE;
    }

    ret = libvirt_buildPyObject(node, "virNetworkPortPtr", NULL);
    return ret;
}

PyObject *
libvirt_virInterfacePtrWrap(virInterfacePtr node)
{
    PyObject *ret;

    if (node == NULL) {
        return VIR_PY_NONE;
    }

    ret = libvirt_buildPyObject(node, "virInterfacePtr", NULL);
    return ret;
}

PyObject *
libvirt_virStoragePoolPtrWrap(virStoragePoolPtr node)
{
    PyObject *ret;

    if (node == NULL) {
        return VIR_PY_NONE;
    }

    ret = libvirt_buildPyObject(node, "virStoragePoolPtr", NULL);
    return ret;
}

PyObject *
libvirt_virStorageVolPtrWrap(virStorageVolPtr node)
{
    PyObject *ret;

    if (node == NULL) {
        return VIR_PY_NONE;
    }

    ret = libvirt_buildPyObject(node, "virStorageVolPtr", NULL);
    return ret;
}

PyObject *
libvirt_virConnectPtrWrap(virConnectPtr node)
{
    PyObject *ret;

    if (node == NULL) {
        return VIR_PY_NONE;
    }

    ret = libvirt_buildPyObject(node, "virConnectPtr", NULL);
    return ret;
}

PyObject *
libvirt_virNodeDevicePtrWrap(virNodeDevicePtr node)
{
    PyObject *ret;

    if (node == NULL) {
        return VIR_PY_NONE;
    }

    ret = libvirt_buildPyObject(node, "virNodeDevicePtr", NULL);
    return ret;
}

PyObject *
libvirt_virSecretPtrWrap(virSecretPtr node)
{
    PyObject *ret;

    if (node == NULL) {
        return VIR_PY_NONE;
    }

    ret = libvirt_buildPyObject(node, "virSecretPtr", NULL);
    return ret;
}

PyObject *
libvirt_virNWFilterPtrWrap(virNWFilterPtr node)
{
    PyObject *ret;

    if (node == NULL) {
        return VIR_PY_NONE;
    }

    ret = libvirt_buildPyObject(node, "virNWFilterPtr", NULL);
    return ret;
}

PyObject *
libvirt_virNWFilterBindingPtrWrap(virNWFilterBindingPtr node)
{
    PyObject *ret;

    if (node == NULL) {
        return VIR_PY_NONE;
    }

    ret = libvirt_buildPyObject(node, "virNWFilterBindingPtr", NULL);
    return ret;
}

PyObject *
libvirt_virStreamPtrWrap(virStreamPtr node)
{
    PyObject *ret;

    if (node == NULL) {
        return VIR_PY_NONE;
    }

    ret = libvirt_buildPyObject(node, "virStreamPtr", NULL);
    return ret;
}

PyObject *
libvirt_virDomainCheckpointPtrWrap(virDomainCheckpointPtr node)
{
    PyObject *ret;

    if (node == NULL) {
        return VIR_PY_NONE;
    }

    ret = libvirt_buildPyObject(node, "virDomainCheckpointPtr", NULL);
    return ret;
}

PyObject *
libvirt_virDomainSnapshotPtrWrap(virDomainSnapshotPtr node)
{
    PyObject *ret;

    if (node == NULL) {
        return VIR_PY_NONE;
    }

    ret = libvirt_buildPyObject(node, "virDomainSnapshotPtr", NULL);
    return ret;
}

PyObject *
libvirt_virEventHandleCallbackWrap(virEventHandleCallback node)
{
    PyObject *ret;

    if (node == NULL) {
        printf("%s: WARNING - Wrapping None\n", __func__);
        return VIR_PY_NONE;
    }

    ret = libvirt_buildPyObject(node, "virEventHandleCallback", NULL);
    return ret;
}

PyObject *
libvirt_virEventTimeoutCallbackWrap(virEventTimeoutCallback node)
{
    PyObject *ret;

    if (node == NULL) {
        printf("%s: WARNING - Wrapping None\n", __func__);
        return VIR_PY_NONE;
    }

    ret = libvirt_buildPyObject(node, "virEventTimeoutCallback", NULL);
    return ret;
}

PyObject *
libvirt_virFreeCallbackWrap(virFreeCallback node)
{
    PyObject *ret;

    if (node == NULL) {
        return VIR_PY_NONE;
    }

    ret = libvirt_buildPyObject(node, "virFreeCallback", NULL);
    return ret;
}

PyObject *
libvirt_virVoidPtrWrap(void* node)
{
    PyObject *ret;

    if (node == NULL) {
        return VIR_PY_NONE;
    }

    ret = libvirt_buildPyObject(node, "void*", NULL);
    return ret;
}
