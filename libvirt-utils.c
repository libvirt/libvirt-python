/*
 * libvirt-utils.c: misc helper APIs for python binding
 *
 * Copyright (C) 2013-2019 Red Hat, Inc.
 *
 * This library is free software; you can redistribute it and/or
 * modify it under the terms of the GNU Lesser General Public
 * License as published by the Free Software Foundation; either
 * version 2.1 of the License, or (at your option) any later version.
 *
 * This library is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 * Lesser General Public License for more details.
 *
 * You should have received a copy of the GNU Lesser General Public
 * License along with this library.  If not, see
 * <http://www.gnu.org/licenses/>.
 *
 */

#include <Python.h>

/* Ugly python defines that, which is also defined in errno.h */
#undef _POSIC_C_SOURCE

/* We want to see *_LAST enums.  */
#define VIR_ENUM_SENTINELS

#include <errno.h>
#include <stddef.h>
#include <stdlib.h>
#include <unistd.h>
#include <libvirt/libvirt.h>
#include "libvirt-utils.h"
#include "typewrappers.h"

/**
 * virAlloc:
 * @ptrptr: pointer to pointer for address of allocated memory
 * @size: number of bytes to allocate
 *
 * Allocate  'size' bytes of memory. Return the address of the
 * allocated memory in 'ptrptr'. The newly allocated memory is
 * filled with zeros.
 *
 * Returns -1 on failure to allocate, zero on success
 */
int
virAlloc(void *ptrptr,
         size_t size)
{
    *(void **)ptrptr = calloc(1, size);
    if (*(void **)ptrptr == NULL) {
        return -1;
    }
    return 0;
}

/**
 * virAllocN:
 * @ptrptr: pointer to pointer for address of allocated memory
 * @size: number of bytes to allocate
 * @count: number of elements to allocate
 *
 * Allocate an array of memory 'count' elements long,
 * each with 'size' bytes. Return the address of the
 * allocated memory in 'ptrptr'.  The newly allocated
 * memory is filled with zeros.
 *
 * Returns -1 on failure to allocate, zero on success
 */
int
virAllocN(void *ptrptr,
          size_t size,
          size_t count)
{
    *(void**)ptrptr = calloc(count, size);
    if (*(void**)ptrptr == NULL) {
        return -1;
    }
    return 0;
}

/**
 * virReallocN:
 * @ptrptr: pointer to pointer for address of allocated memory
 * @size: number of bytes to allocate
 * @count: number of elements in array
 *
 * Resize the block of memory in 'ptrptr' to be an array of
 * 'count' elements, each 'size' bytes in length. Update 'ptrptr'
 * with the address of the newly allocated memory. On failure,
 * 'ptrptr' is not changed and still points to the original memory
 * block. Any newly allocated memory in 'ptrptr' is uninitialized.
 *
 * Returns -1 on failure to allocate, zero on success
 */
int
virReallocN(void *ptrptr,
            size_t size,
            size_t count)
{
    void *tmp;

    if (xalloc_oversized(count, size)) {
        errno = ENOMEM;
        return -1;
    }
    tmp = realloc(*(void**)ptrptr, size * count);
    if (!tmp && ((size * count) != 0)) {
        return -1;
    }
    *(void**)ptrptr = tmp;
    return 0;
}


/**
 * virFree:
 * @ptrptr: pointer to pointer for address of memory to be freed
 *
 * Release the chunk of memory in the pointer pointed to by
 * the 'ptrptr' variable. After release, 'ptrptr' will be
 * updated to point to NULL.
 */
void
virFree(void *ptrptr)
{
    int save_errno = errno;

    free(*(void**)ptrptr);
    *(void**)ptrptr = NULL;
    errno = save_errno;
}


int
virFileClose(int *fdptr)
{
    int saved_errno = 0;
    int rc = 0;

    saved_errno = errno;

    if (*fdptr < 0)
        return 0;

    rc = close(*fdptr);
    *fdptr = -1;

    errno = saved_errno;

    return rc;
}

#if ! LIBVIR_CHECK_VERSION(1, 0, 2)
/**
 * virTypedParamsClear:
 * @params: the array of the typed parameters
 * @nparams: number of parameters in the @params array
 *
 * Frees all memory used by string parameters. The memory occupied by @params
 * is not free; use virTypedParamsFree if you want it to be freed too.
 *
 * Returns nothing.
 */
void
virTypedParamsClear(virTypedParameterPtr params,
                    int nparams)
{
    size_t i;

    if (!params)
        return;

    for (i = 0; i < nparams; i++) {
        if (params[i].type == VIR_TYPED_PARAM_STRING)
            VIR_FREE(params[i].value.s);
    }
}

/**
 * virTypedParamsFree:
 * @params: the array of the typed parameters
 * @nparams: number of parameters in the @params array
 *
 * Frees all memory used by string parameters and the memory occuiped by
 * @params.
 *
 * Returns nothing.
 */
void
virTypedParamsFree(virTypedParameterPtr params,
                   int nparams)
{
    virTypedParamsClear(params, nparams);
    VIR_FREE(params);
}
#endif /* ! LIBVIR_CHECK_VERSION(1, 0, 2) */

/* Helper function to convert a virTypedParameter output array into a
 * Python dictionary for return to the user.  Return NULL on failure,
 * after raising a python exception.  */
PyObject *
getPyVirTypedParameter(const virTypedParameter *params,
                       int nparams)
{
    PyObject *key, *val, *info;
    ssize_t i;

    if ((info = PyDict_New()) == NULL)
        return NULL;

    for (i = 0; i < nparams; i++) {
        switch (params[i].type) {
        case VIR_TYPED_PARAM_INT:
            val = libvirt_intWrap(params[i].value.i);
            break;

        case VIR_TYPED_PARAM_UINT:
            val = libvirt_intWrap(params[i].value.ui);
            break;

        case VIR_TYPED_PARAM_LLONG:
            val = libvirt_longlongWrap(params[i].value.l);
            break;

        case VIR_TYPED_PARAM_ULLONG:
            val = libvirt_ulonglongWrap(params[i].value.ul);
            break;

        case VIR_TYPED_PARAM_DOUBLE:
            val = PyFloat_FromDouble(params[i].value.d);
            break;

        case VIR_TYPED_PARAM_BOOLEAN:
            val = PyBool_FromLong(params[i].value.b);
            break;

        case VIR_TYPED_PARAM_STRING:
            val = libvirt_constcharPtrWrap(params[i].value.s);
            break;

        default:
            /* Possible if a newer server has a bug and sent stuff we
             * don't recognize.  */
            PyErr_Format(PyExc_LookupError,
                         "Type value \"%d\" not recognized",
                         params[i].type);
            val = NULL;
            break;
        }

        key = libvirt_constcharPtrWrap(params[i].field);

        VIR_PY_DICT_SET_GOTO(info, key, val, cleanup);
    }
    return info;

 cleanup:
    Py_DECREF(info);
    return NULL;
}

/* Allocate a new typed parameter array with the same contents and
 * length as info, and using the array params of length nparams as
 * hints on what types to use when creating the new array. The caller
 * must clear the array before freeing it. Return NULL on failure,
 * after raising a python exception.  */
virTypedParameterPtr
setPyVirTypedParameter(PyObject *info,
                       const virTypedParameter *params,
                       int nparams)
{
    PyObject *key, *value;
    Py_ssize_t pos = 0;
    virTypedParameterPtr temp = NULL, ret = NULL;
    Py_ssize_t size;
    ssize_t i;

    if ((size = PyDict_Size(info)) < 0)
        return NULL;

    /* Libvirt APIs use NULL array and 0 size as a special case;
     * setting should have at least one parameter.  */
    if (size == 0) {
        PyErr_Format(PyExc_LookupError, "Dictionary must not be empty");
        return NULL;
    }

    if (VIR_ALLOC_N(ret, size) < 0) {
        PyErr_NoMemory();
        return NULL;
    }

    temp = &ret[0];
    while (PyDict_Next(info, &pos, &key, &value)) {
        char *keystr = NULL;

        if (libvirt_charPtrUnwrap(key, &keystr) < 0)
            goto cleanup;

        for (i = 0; i < nparams; i++) {
            if (STREQ(params[i].field, keystr))
                break;
        }
        if (i == nparams) {
            PyErr_Format(PyExc_LookupError,
                         "Attribute name \"%s\" could not be recognized",
                         keystr);
            VIR_FREE(keystr);
            goto cleanup;
        }

        strncpy(temp->field, keystr, VIR_TYPED_PARAM_FIELD_LENGTH - 1);
        temp->type = params[i].type;
        VIR_FREE(keystr);

        switch (params[i].type) {
        case VIR_TYPED_PARAM_INT:
            if (libvirt_intUnwrap(value, &temp->value.i) < 0)
                goto cleanup;
            break;

        case VIR_TYPED_PARAM_UINT:
            if (libvirt_uintUnwrap(value, &temp->value.ui) < 0)
                goto cleanup;
            break;

        case VIR_TYPED_PARAM_LLONG:
            if (libvirt_longlongUnwrap(value, &temp->value.l) < 0)
                goto cleanup;
            break;

        case VIR_TYPED_PARAM_ULLONG:
            if (libvirt_ulonglongUnwrap(value, &temp->value.ul) < 0)
                goto cleanup;
            break;

        case VIR_TYPED_PARAM_DOUBLE:
            if (libvirt_doubleUnwrap(value, &temp->value.d) < 0)
                goto cleanup;
            break;

        case VIR_TYPED_PARAM_BOOLEAN:
        {
            bool b;
            if (libvirt_boolUnwrap(value, &b) < 0)
                goto cleanup;
            temp->value.b = b;
            break;
        }
        case VIR_TYPED_PARAM_STRING:
        {
            char *string_val;
            if (libvirt_charPtrUnwrap(value, &string_val) < 0)
                goto cleanup;
            temp->value.s = string_val;
            break;
        }

        default:
            /* Possible if a newer server has a bug and sent stuff we
             * don't recognize.  */
            PyErr_Format(PyExc_LookupError,
                         "Type value \"%d\" not recognized",
                         params[i].type);
            goto cleanup;
        }

        temp++;
    }
    return ret;

 cleanup:
    virTypedParamsFree(ret, size);
    return NULL;
}


/* While these appeared in libvirt in 1.0.2, we only
 * need them in the python from 1.1.0 onwards */
#if LIBVIR_CHECK_VERSION(1, 1, 0)
int
virPyDictToTypedParamOne(virTypedParameterPtr *params,
                         int *n,
                         int *max,
                         virPyTypedParamsHintPtr hints,
                         int nhints,
                         const char *keystr,
                         PyObject *value)
{
    int rv = -1, type = -1;
    ssize_t i;

    for (i = 0; i < nhints; i++) {
        if (STREQ(hints[i].name, keystr)) {
            type = hints[i].type;
            break;
        }
    }

    if (type == -1) {
        if (libvirt_PyString_Check(value)) {
            type = VIR_TYPED_PARAM_STRING;
        } else if (PyBool_Check(value)) {
            type = VIR_TYPED_PARAM_BOOLEAN;
        } else if (PyLong_Check(value)) {
            unsigned long long ull = PyLong_AsUnsignedLongLong(value);
            if (ull == (unsigned long long) -1 && PyErr_Occurred())
                type = VIR_TYPED_PARAM_LLONG;
            else
                type = VIR_TYPED_PARAM_ULLONG;
        } else if (PyFloat_Check(value)) {
            type = VIR_TYPED_PARAM_DOUBLE;
        }
    }

    if (type == -1) {
        PyErr_Format(PyExc_TypeError,
                     "Unknown type of \"%s\" field", keystr);
        goto cleanup;
    }

    switch ((virTypedParameterType) type) {
    case VIR_TYPED_PARAM_INT:
    {
        int val;
        if (libvirt_intUnwrap(value, &val) < 0 ||
            virTypedParamsAddInt(params, n, max, keystr, val) < 0)
            goto cleanup;
        break;
    }
    case VIR_TYPED_PARAM_UINT:
    {
        unsigned int val;
        if (libvirt_uintUnwrap(value, &val) < 0 ||
            virTypedParamsAddUInt(params, n, max, keystr, val) < 0)
            goto cleanup;
        break;
    }
    case VIR_TYPED_PARAM_LLONG:
    {
        long long val;
        if (libvirt_longlongUnwrap(value, &val) < 0 ||
            virTypedParamsAddLLong(params, n, max, keystr, val) < 0)
            goto cleanup;
        break;
    }
    case VIR_TYPED_PARAM_ULLONG:
    {
        unsigned long long val;
        if (libvirt_ulonglongUnwrap(value, &val) < 0 ||
            virTypedParamsAddULLong(params, n, max, keystr, val) < 0)
            goto cleanup;
        break;
    }
    case VIR_TYPED_PARAM_DOUBLE:
    {
        double val;
        if (libvirt_doubleUnwrap(value, &val) < 0 ||
            virTypedParamsAddDouble(params, n, max, keystr, val) < 0)
            goto cleanup;
        break;
    }
    case VIR_TYPED_PARAM_BOOLEAN:
    {
        bool val;
        if (libvirt_boolUnwrap(value, &val) < 0 ||
            virTypedParamsAddBoolean(params, n, max, keystr, val) < 0)
            goto cleanup;
        break;
    }
    case VIR_TYPED_PARAM_STRING:
    {
        char *val;;
        if (libvirt_charPtrUnwrap(value, &val) < 0 ||
            virTypedParamsAddString(params, n, max, keystr, val) < 0) {
            VIR_FREE(val);
            goto cleanup;
        }
        VIR_FREE(val);
        break;
    }
    case VIR_TYPED_PARAM_LAST:
        break; /* unreachable */
    }

    rv = 0;

 cleanup:
    return rv;
}


/* Automatically convert dict into type parameters based on types reported
 * by python. All integer types are converted into LLONG (in case of a negative
 * value) or ULLONG (in case of a positive value). If you need different
 * handling, use @hints to explicitly specify what types should be used for
 * specific parameters.
 */
int
virPyDictToTypedParams(PyObject *dict,
                       virTypedParameterPtr *ret_params,
                       int *ret_nparams,
                       virPyTypedParamsHintPtr hints,
                       int nhints)
{
    PyObject *key;
    PyObject *value;
    Py_ssize_t pos = 0;
    virTypedParameterPtr params = NULL;
    int n = 0;
    int max = 0;
    int ret = -1;
    char *keystr = NULL;

    *ret_params = NULL;
    *ret_nparams = 0;

    if (PyDict_Size(dict) < 0)
        return -1;

    while (PyDict_Next(dict, &pos, &key, &value)) {
        if (libvirt_charPtrUnwrap(key, &keystr) < 0)
            goto cleanup;

        if (PyList_Check(value) || PyTuple_Check(value)) {
            Py_ssize_t i, size = PySequence_Size(value);

            for (i = 0; i < size; i++) {
                PyObject *v = PySequence_ITEM(value, i);
                if (virPyDictToTypedParamOne(&params, &n, &max,
                                             hints, nhints, keystr, v) < 0)
                    goto cleanup;
            }
        } else if (virPyDictToTypedParamOne(&params, &n, &max,
                                            hints, nhints, keystr, value) < 0)
            goto cleanup;

        VIR_FREE(keystr);
    }

    *ret_params = params;
    *ret_nparams = n;
    params = NULL;
    ret = 0;

 cleanup:
    VIR_FREE(keystr);
    virTypedParamsFree(params, n);
    return ret;
}
#endif /* LIBVIR_CHECK_VERSION(1, 1, 0) */


/* virPyCpumapConvert
 * @cpunum: the number of physical cpus of the host.
 * @pycpumap: source cpu map, python tuple of bools.
 * @cpumapptr: destination cpu map.
 * @cpumaplen: destination cpu map length.
 *
 * Helper function to convert a pycpumap to char*.
 *
 * Returns 0 on success, -1 on failure with error set.
 */
int
virPyCpumapConvert(int cpunum,
                   PyObject *pycpumap,
                   unsigned char **cpumapptr,
                   int *cpumaplen)
{
    int tuple_size;
    ssize_t i;
    *cpumapptr = NULL;

    if (!PyTuple_Check(pycpumap)) {
        PyErr_SetString(PyExc_TypeError, "Unexpected type, tuple is required");
        return -1;
    }

    *cpumaplen = VIR_CPU_MAPLEN(cpunum);

    if ((tuple_size = PyTuple_Size(pycpumap)) == -1)
        return -1;

    if (VIR_ALLOC_N(*cpumapptr, *cpumaplen) < 0) {
        PyErr_NoMemory();
        return -1;
    }

    for (i = 0; i < cpunum && i < tuple_size; i++) {
        PyObject *flag = PyTuple_GetItem(pycpumap, i);
        bool b;

        if (!flag || libvirt_boolUnwrap(flag, &b) < 0) {
            VIR_FREE(*cpumapptr);
            return -1;
        }

        if (b)
            VIR_USE_CPU(*cpumapptr, i);
    }

    return 0;
}
