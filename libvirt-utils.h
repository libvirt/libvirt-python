/*
 * libvirt-utils.h: misc helper APIs for python binding
 *
 * Copyright (C) 2013 Red Hat, Inc.
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

#ifndef __LIBVIRT_UTILS_H__
# define __LIBVIRT_UTILS_H__

# define STREQ(a,b) (strcmp(a,b) == 0)

# ifndef MIN
#  define MIN(a,b) (((a) < (b)) ? (a) : (b))
# endif

/**
 * libvirt.h provides this as of version 1.2.0, but we want to be able
 * to support older versions of libvirt so copy and paste the macro from
 * libvirt.h
 */
# ifndef LIBVIR_CHECK_VERSION
#  define LIBVIR_CHECK_VERSION(major, minor, micro) \
    ((major) * 1000000 + (minor) * 1000 + (micro) <= LIBVIR_VERSION_NUMBER)
# endif

/* Return 1 if an array of N objects, each of size S, cannot exist due
   to size arithmetic overflow.  S must be positive and N must be
   nonnegative.  This is a macro, not a function, so that it
   works correctly even when SIZE_MAX < N.

   By gnulib convention, SIZE_MAX represents overflow in size
   calculations, so the conservative dividend to use here is
   SIZE_MAX - 1, since SIZE_MAX might represent an overflowed value.
   However, malloc (SIZE_MAX) fails on all known hosts where
   sizeof (ptrdiff_t) <= sizeof (size_t), so do not bother to test for
   exactly-SIZE_MAX allocations on such hosts; this avoids a test and
   branch when S is known to be 1.  */
# define xalloc_oversized(n, s) \
    ((size_t) (sizeof (ptrdiff_t) <= sizeof (size_t) ? -1 : -2) / (s) < (n))


/* The __attribute__((__warn_unused_result__)) feature
   is available in gcc versions 3.4 and newer,
   while the typeof feature has been available since 2.7 at least.  */
# if 3 < __GNUC__ + (4 <= __GNUC_MINOR__)
#  define ignore_value(x) \
    (__extension__ ({ __typeof__ (x) __x = (x); (void) __x; }))
# else
#  define ignore_value(x) ((void) (x))
# endif

# ifdef __GNUC__

#  ifndef __GNUC_PREREQ
#   if defined __GNUC__ && defined __GNUC_MINOR__
#    define __GNUC_PREREQ(maj, min)                                        \
    ((__GNUC__ << 16) + __GNUC_MINOR__ >= ((maj) << 16) + (min))
#   else
#    define __GNUC_PREREQ(maj, min) 0
#   endif
#  endif /* __GNUC_PREREQ */

/**
 * ATTRIBUTE_UNUSED:
 *
 * Macro to flag consciously unused parameters to functions
 */
#  ifndef ATTRIBUTE_UNUSED
#   define ATTRIBUTE_UNUSED __attribute__((__unused__))
#  endif

/* gcc's handling of attribute nonnull is less than stellar - it does
 * NOT improve diagnostics, and merely allows gcc to optimize away
 * null code checks even when the caller manages to pass null in spite
 * of the attribute, leading to weird crashes.  Coverity, on the other
 * hand, knows how to do better static analysis based on knowing
 * whether a parameter is nonnull.  Make this attribute conditional
 * based on whether we are compiling for real or for analysis, while
 * still requiring correct gcc syntax when it is turned off.  See also
 * http://gcc.gnu.org/bugzilla/show_bug.cgi?id=17308 */
#  ifndef ATTRIBUTE_NONNULL
#   if __GNUC_PREREQ (3, 3)
#    if STATIC_ANALYSIS
#     define ATTRIBUTE_NONNULL(m) __attribute__((__nonnull__(m)))
#    else
#     define ATTRIBUTE_NONNULL(m) __attribute__(())
#    endif
#   else
#    define ATTRIBUTE_NONNULL(m)
#   endif
#  endif

#  ifndef ATTRIBUTE_RETURN_CHECK
#   if __GNUC_PREREQ (3, 4)
#    define ATTRIBUTE_RETURN_CHECK __attribute__((__warn_unused_result__))
#   else
#    define ATTRIBUTE_RETURN_CHECK
#   endif
#  endif

# else
#  ifndef ATTRIBUTE_UNUSED
#   define ATTRIBUTE_UNUSED
#  endif
#  ifndef ATTRIBUTE_NONNULL
#   define ATTRIBUTE_NONNULL(m)
#  endif
#  ifndef ATTRIBUTE_RETURN_CHECK
#   define ATTRIBUTE_RETURN_CHECK
#  endif
# endif                         /* __GNUC__ */


/* Don't call these directly - use the macros below */
int virAlloc(void *ptrptr, size_t size)
    ATTRIBUTE_RETURN_CHECK ATTRIBUTE_NONNULL(1);
int virAllocN(void *ptrptr, size_t size, size_t count)
    ATTRIBUTE_RETURN_CHECK ATTRIBUTE_NONNULL(1);
int virReallocN(void *ptrptr, size_t size, size_t count)
    ATTRIBUTE_RETURN_CHECK ATTRIBUTE_NONNULL(1);
void virFree(void *ptrptr) ATTRIBUTE_NONNULL(1);

/**
 * VIR_ALLOC:
 * @ptr: pointer to hold address of allocated memory
 *
 * Allocate sizeof(*ptr) bytes of memory and store
 * the address of allocated memory in 'ptr'. Fill the
 * newly allocated memory with zeros.
 *
 * This macro is safe to use on arguments with side effects.
 *
 * Returns -1 on failure (with OOM error reported), 0 on success
 */
# define VIR_ALLOC(ptr) virAlloc(&(ptr), sizeof(*(ptr)))

/**
 * VIR_ALLOC_N:
 * @ptr: pointer to hold address of allocated memory
 * @count: number of elements to allocate
 *
 * Allocate an array of 'count' elements, each sizeof(*ptr)
 * bytes long and store the address of allocated memory in
 * 'ptr'. Fill the newly allocated memory with zeros.
 *
 * This macro is safe to use on arguments with side effects.
 *
 * Returns -1 on failure (with OOM error reported), 0 on success
 */
# define VIR_ALLOC_N(ptr, count) virAllocN(&(ptr), sizeof(*(ptr)), (count))

/**
 * VIR_REALLOC_N:
 * @ptr: pointer to hold address of allocated memory
 * @count: number of elements to allocate
 *
 * Re-allocate an array of 'count' elements, each sizeof(*ptr)
 * bytes long and store the address of allocated memory in
 * 'ptr'. If 'ptr' grew, the added memory is uninitialized.
 *
 * This macro is safe to use on arguments with side effects.
 *
 * Returns -1 on failure (with OOM error reported), 0 on success
 */
# define VIR_REALLOC_N(ptr, count) virReallocN(&(ptr), sizeof(*(ptr)), (count))

/**
 * VIR_FREE:
 * @ptr: pointer holding address to be freed
 *
 * Free the memory stored in 'ptr' and update to point
 * to NULL.
 *
 * This macro is safe to use on arguments with side effects.
 */
# if !STATIC_ANALYSIS
/* The ternary ensures that ptr is a pointer and not an integer type,
 * while evaluating ptr only once.  This gives us extra compiler
 * safety when compiling under gcc.  For now, we intentionally cast
 * away const, since a number of callers safely pass const char *.
 */
#  define VIR_FREE(ptr) virFree((void *) (1 ? (const void *) &(ptr) : (ptr)))
# else
/* The Coverity static analyzer considers the else path of the "?:" and
 * flags the VIR_FREE() of the address of the address of memory as a
 * RESOURCE_LEAK resulting in numerous false positives (eg, VIR_FREE(&ptr))
 */
#  define VIR_FREE(ptr) virFree((void *) &(ptr))
# endif

/* Don't call this directly - use the macro below */
int virFileClose(int *fdptr)
        ATTRIBUTE_RETURN_CHECK;

# define VIR_FORCE_CLOSE(FD) \
    ignore_value(virFileClose(&(FD)))

# if ! LIBVIR_CHECK_VERSION(1, 0, 2)
void virTypedParamsClear(virTypedParameterPtr params, int nparams);

void virTypedParamsFree(virTypedParameterPtr params, int nparams);
# endif /* ! LIBVIR_CHECK_VERSION(1, 0, 2) */

#endif /* __LIBVIRT_UTILS_H__ */
