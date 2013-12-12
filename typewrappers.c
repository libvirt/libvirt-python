/*
 * types.c: converter functions between the internal representation
 *          and the Python objects
 *
 * Copyright (C) 2005, 2007, 2012 Red Hat, Inc.
 *
 * Daniel Veillard <veillard@redhat.com>
 */

/* Horrible kludge to work around even more horrible name-space pollution
 *    via Python.h.  That file includes /usr/include/python2.5/pyconfig*.h,
 *       which has over 180 autoconf-style HAVE_* definitions.  Shame on them.  */
#undef HAVE_PTHREAD_H

#include "typewrappers.h"
#include "libvirt-utils.h"

#ifndef Py_CAPSULE_H
typedef void(*PyCapsule_Destructor)(void *, void *);
#endif

static PyObject *
libvirt_buildPyObject(void *cobj,
                      const char *name,
                      PyCapsule_Destructor destr)
{
    PyObject *ret;

#ifdef Py_CAPSULE_H
    ret = PyCapsule_New(cobj, name, destr);
#else
    ret = PyCObject_FromVoidPtrAndDesc(cobj, (void *) name, destr);
#endif /* _TEST_CAPSULE */

    return ret;
}

PyObject *
libvirt_intWrap(int val)
{
    PyObject *ret;
#if PY_MAJOR_VERSION > 2
    ret = PyLong_FromLong((long) val);
#else
    ret = PyInt_FromLong((long) val);
#endif
    return ret;
}

PyObject *
libvirt_uintWrap(uint val)
{
    PyObject *ret;
#if PY_MAJOR_VERSION > 2
    ret = PyLong_FromLong((long) val);
#else
    ret = PyInt_FromLong((long) val);
#endif
    return ret;
}

PyObject *
libvirt_longWrap(long val)
{
    PyObject *ret;
    ret = PyLong_FromLong(val);
    return ret;
}

PyObject *
libvirt_ulongWrap(unsigned long val)
{
    PyObject *ret;
    ret = PyLong_FromLong(val);
    return ret;
}

PyObject *
libvirt_longlongWrap(long long val)
{
    PyObject *ret;
    ret = PyLong_FromUnsignedLongLong((unsigned long long) val);
    return ret;
}

PyObject *
libvirt_ulonglongWrap(unsigned long long val)
{
    PyObject *ret;
    ret = PyLong_FromUnsignedLongLong(val);
    return ret;
}

PyObject *
libvirt_charPtrSizeWrap(char *str, Py_ssize_t size)
{
    PyObject *ret;

    if (str == NULL) {
        Py_INCREF(Py_None);
        return Py_None;
    }
#if PY_MAJOR_VERSION > 2
    ret = PyBytes_FromStringAndSize(str, size);
#else
    ret = PyString_FromStringAndSize(str, size);
#endif
    return ret;
}

PyObject *
libvirt_charPtrWrap(char *str)
{
    PyObject *ret;

    if (str == NULL) {
        Py_INCREF(Py_None);
        return Py_None;
    }
#if PY_MAJOR_VERSION > 2
    ret = PyUnicode_FromString(str);
#else
    ret = PyString_FromString(str);
#endif
    return ret;
}

PyObject *
libvirt_constcharPtrWrap(const char *str)
{
    PyObject *ret;

    if (str == NULL) {
        Py_INCREF(Py_None);
        return Py_None;
    }
#if PY_MAJOR_VERSION > 2
    ret = PyUnicode_FromString(str);
#else
    ret = PyString_FromString(str);
#endif
    return ret;
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
libvirt_intUnwrap(PyObject *obj, int *val)
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
#if PY_MAJOR_VERSION > 2
    long_val = PyLong_AsLong(obj);
#else
    long_val = PyInt_AsLong(obj);
#endif
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
libvirt_uintUnwrap(PyObject *obj, unsigned int *val)
{
    long long_val;

    if (!obj) {
        PyErr_SetString(PyExc_TypeError, "unexpected type");
        return -1;
    }

#if PY_MAJOR_VERSION > 2
    long_val = PyLong_AsLong(obj);
#else
    long_val = PyInt_AsLong(obj);
#endif
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
libvirt_longUnwrap(PyObject *obj, long *val)
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
libvirt_ulongUnwrap(PyObject *obj, unsigned long *val)
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
libvirt_longlongUnwrap(PyObject *obj, long long *val)
{
    long long llong_val = -1;

    if (!obj) {
        PyErr_SetString(PyExc_TypeError, "unexpected type");
        return -1;
    }

#if PY_MAJOR_VERSION == 2
    /* If obj is of PyInt_Type, PyLong_AsLongLong
     * will call PyInt_AsLong() to handle it automatically.
     */
    if (PyInt_Check(obj) || PyLong_Check(obj))
#else
    if (PyLong_Check(obj))
#endif
        llong_val = PyLong_AsLongLong(obj);
    else
        PyErr_SetString(PyExc_TypeError, "an integer is required");

    if ((llong_val == -1) && PyErr_Occurred())
        return -1;

    *val = llong_val;
    return 0;
}

int
libvirt_ulonglongUnwrap(PyObject *obj, unsigned long long *val)
{
    unsigned long long ullong_val = -1;

    if (!obj) {
        PyErr_SetString(PyExc_TypeError, "unexpected type");
        return -1;
    }

#if PY_MAJOR_VERSION == 2
    /* The PyLong_AsUnsignedLongLong doesn't check the type of
     * obj, only accept argument of PyLong_Type, so we check it instead.
     */
    if (PyInt_Check(obj)) {
        long long llong_val = PyInt_AsLong(obj);
        if (llong_val < 0)
            PyErr_SetString(PyExc_OverflowError,
                            "negative Python int cannot be converted to C unsigned long long");
        else
            ullong_val = llong_val;
    } else if (PyLong_Check(obj)) {
#else
    if (PyLong_Check(obj)) {
#endif
        ullong_val = PyLong_AsUnsignedLongLong(obj);
    } else {
        PyErr_SetString(PyExc_TypeError, "an integer is required");
    }

    if ((ullong_val == -1) && PyErr_Occurred())
        return -1;

    *val = ullong_val;
    return 0;
}

int
libvirt_doubleUnwrap(PyObject *obj, double *val)
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
libvirt_boolUnwrap(PyObject *obj, bool *val)
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
libvirt_charPtrUnwrap(PyObject *obj, char **str)
{
#if PY_MAJOR_VERSION > 2
    PyObject *bytes;
#endif
    const char *ret;
    *str = NULL;
    if (!obj) {
        PyErr_SetString(PyExc_TypeError, "unexpected type");
        return -1;
    }

#if PY_MAJOR_VERSION > 2
    if (!(bytes = PyUnicode_AsUTF8String(obj)))
        return -1;
    ret = PyBytes_AsString(bytes);
#else
    ret = PyString_AsString(obj);
#endif
    if (ret)
        *str = strdup(ret);
#if PY_MAJOR_VERSION > 2
    Py_DECREF(bytes);
#endif
    return ret && *str ? 0 : -1;
}

int libvirt_charPtrSizeUnwrap(PyObject *obj, char **str, Py_ssize_t *size)
{
    int ret;
#if PY_MAJOR_VERSION == 2 && PY_MINOR_VERSION <= 4
    int isize;
#endif
    *str = NULL;
    *size = 0;
    if (!obj) {
        PyErr_SetString(PyExc_TypeError, "unexpected type");
        return -1;
    }

#if PY_MAJOR_VERSION > 2
    ret = PyBytes_AsStringAndSize(obj, str, size);
#else
# if PY_MINOR_VERSION <= 4
    ret = PyString_AsStringAndSize(obj, str, &isize);
    *size = isize;
# else
    ret = PyString_AsStringAndSize(obj, str, size);
# endif
#endif

    return ret;
}

PyObject *
libvirt_virDomainPtrWrap(virDomainPtr node)
{
    PyObject *ret;

    if (node == NULL) {
        Py_INCREF(Py_None);
        return Py_None;
    }

    ret = libvirt_buildPyObject(node, "virDomainPtr", NULL);
    return ret;
}

PyObject *
libvirt_virNetworkPtrWrap(virNetworkPtr node)
{
    PyObject *ret;

    if (node == NULL) {
        Py_INCREF(Py_None);
        return Py_None;
    }

    ret = libvirt_buildPyObject(node, "virNetworkPtr", NULL);
    return ret;
}

PyObject *
libvirt_virInterfacePtrWrap(virInterfacePtr node)
{
    PyObject *ret;

    if (node == NULL) {
        Py_INCREF(Py_None);
        return Py_None;
    }

    ret = libvirt_buildPyObject(node, "virInterfacePtr", NULL);
    return ret;
}

PyObject *
libvirt_virStoragePoolPtrWrap(virStoragePoolPtr node)
{
    PyObject *ret;

    if (node == NULL) {
        Py_INCREF(Py_None);
        return Py_None;
    }

    ret = libvirt_buildPyObject(node, "virStoragePoolPtr", NULL);
    return ret;
}

PyObject *
libvirt_virStorageVolPtrWrap(virStorageVolPtr node)
{
    PyObject *ret;

    if (node == NULL) {
        Py_INCREF(Py_None);
        return Py_None;
    }

    ret = libvirt_buildPyObject(node, "virStorageVolPtr", NULL);
    return ret;
}

PyObject *
libvirt_virConnectPtrWrap(virConnectPtr node)
{
    PyObject *ret;

    if (node == NULL) {
        Py_INCREF(Py_None);
        return Py_None;
    }

    ret = libvirt_buildPyObject(node, "virConnectPtr", NULL);
    return ret;
}

PyObject *
libvirt_virNodeDevicePtrWrap(virNodeDevicePtr node)
{
    PyObject *ret;

    if (node == NULL) {
        Py_INCREF(Py_None);
        return Py_None;
    }

    ret = libvirt_buildPyObject(node, "virNodeDevicePtr", NULL);
    return ret;
}

PyObject *
libvirt_virSecretPtrWrap(virSecretPtr node)
{
    PyObject *ret;

    if (node == NULL) {
        Py_INCREF(Py_None);
        return Py_None;
    }

    ret = libvirt_buildPyObject(node, "virSecretPtr", NULL);
    return ret;
}

PyObject *
libvirt_virNWFilterPtrWrap(virNWFilterPtr node)
{
    PyObject *ret;

    if (node == NULL) {
        Py_INCREF(Py_None);
        return Py_None;
    }

    ret = libvirt_buildPyObject(node, "virNWFilterPtr", NULL);
    return ret;
}

PyObject *
libvirt_virStreamPtrWrap(virStreamPtr node)
{
    PyObject *ret;

    if (node == NULL) {
        Py_INCREF(Py_None);
        return Py_None;
    }

    ret = libvirt_buildPyObject(node, "virStreamPtr", NULL);
    return ret;
}

PyObject *
libvirt_virDomainSnapshotPtrWrap(virDomainSnapshotPtr node)
{
    PyObject *ret;

    if (node == NULL) {
        Py_INCREF(Py_None);
        return Py_None;
    }

    ret = libvirt_buildPyObject(node, "virDomainSnapshotPtr", NULL);
    return ret;
}

PyObject *
libvirt_virEventHandleCallbackWrap(virEventHandleCallback node)
{
    PyObject *ret;

    if (node == NULL) {
        Py_INCREF(Py_None);
        printf("%s: WARNING - Wrapping None\n", __func__);
        return Py_None;
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
        Py_INCREF(Py_None);
        return Py_None;
    }

    ret = libvirt_buildPyObject(node, "virEventTimeoutCallback", NULL);
    return ret;
}

PyObject *
libvirt_virFreeCallbackWrap(virFreeCallback node)
{
    PyObject *ret;

    if (node == NULL) {
        Py_INCREF(Py_None);
        return Py_None;
    }

    ret = libvirt_buildPyObject(node, "virFreeCallback", NULL);
    return ret;
}

PyObject *
libvirt_virVoidPtrWrap(void* node)
{
    PyObject *ret;

    if (node == NULL) {
        Py_INCREF(Py_None);
        return Py_None;
    }

    ret = libvirt_buildPyObject(node, "void*", NULL);
    return ret;
}
