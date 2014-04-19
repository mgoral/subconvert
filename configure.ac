AC_INIT([Subconvert], [1.0.3], [https://github.com/mgoral/subconvert/issues])
AM_INIT_AUTOMAKE([foreign -Wall])

AC_PREFIX_DEFAULT([/usr])

AC_CONFIG_FILES([
    Makefile
    subconvert/Makefile
    subconvert/cli/Makefile
    subconvert/gui/Makefile
    subconvert/parsing/Makefile
    subconvert/utils/Makefile
    icons/Makefile
    img/Makefile
    po/Makefile.in
])

AM_PATH_PYTHON([3.2])
AC_PROG_LN_S
AC_PROG_MKDIR_P

AM_GNU_GETTEXT_VERSION([0.17])
AM_GNU_GETTEXT([external], [need-ngettext])
IT_PROG_INTLTOOL([0.35.0])

GETTEXT_PACKAGE=AC_PACKAGE_TARNAME
AC_SUBST(GETTEXT_PACKAGE)
AC_DEFINE_UNQUOTED(GETTEXT_PACKAGE,"$GETTEXT_PACKAGE", [gettext package])

AC_CHECK_PROGS([PYRCC], [pyrcc4], [:])
if test "$PYRCC" = :; then
    AC_MSG_ERROR([Could not find program: pyrcc4])
fi

AC_CHECK_PROGS([MPLAYER], [mplayer], [:])
if test "$MPLAYER" = :; then
    AC_MSG_ERROR([Could not find program: mplayer])
fi


AM_CHECK_PYMOD(chardet,,,[AC_MSG_ERROR(Could not find python module: chardet)])
AM_CHECK_PYMOD(PyQt4,,,[AC_MSG_ERROR(Could not find python module: PyQt4)])

AC_OUTPUT([
    subconvert/utils/Locale.py
    subconvert/utils/version.py
])

echo ""
echo "Subconvert options:"
echo "Prefix: ${prefix}"
