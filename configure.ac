
AC_INIT([lb], [0.3.0], [bugs-lb@inaugust.com])
AC_CONFIG_AUX_DIR(config)
AM_INIT_AUTOMAKE(nostdinc subdir-objects foreign)
AC_CONFIG_SRCDIR([lb/lb.cc])
AM_CONFIG_HEADER(config.h)
AC_CONFIG_MACRO_DIR([m4])


LT_INIT
LT_LANG(C++)

# Checks for libraries.
# FIXME: Replace `main' with a function in `-lexpat':
AC_CHECK_LIB([expat], [main])
# FIXME: Replace `main' with a function in `-libs':
AC_CHECK_LIB([ibs], [main])
AC_LANG_PUSH(C++)
# FIXME: Replace `main' with a function in `-lomniDynamic3':
AC_CHECK_LIB([omniDynamic4], [main])
# FIXME: Replace `main' with a function in `-lomniGK_stub':
AC_CHECK_LIB([omniGK_stub], [main])
# FIXME: Replace `main' with a function in `-lomniORB3':
AC_CHECK_LIB([omniORB4], [main])
# FIXME: Replace `main' with a function in `-lomnithread':
AC_CHECK_LIB([omnithread], [main])
AC_LANG_POP()

AC_CHECK_LIB([dl], [dlopen])


ACX_PTHREAD
AM_PATH_PYTHON
CXXFLAGS="${PTHREAD_CFLAGS} ${CXXFLAGS}"



# Checks for header files.
AC_HEADER_STDC
AC_CHECK_HEADERS([errno.h fcntl.h stdlib.h string.h sys/time.h unistd.h])

# Checks for typedefs, structures, and compiler characteristics.
AC_C_CONST
AC_C_INLINE
AC_HEADER_TIME

# Checks for library functions.
AC_FUNC_MALLOC
AC_CHECK_FUNCS([gettimeofday pow sqrt strdup strrchr])

AC_CONFIG_FILES([ Makefile ])
AC_OUTPUT
