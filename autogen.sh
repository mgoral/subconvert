#!/bin/sh

echo "Preparing Subconvert build system..."

autoreconf --force --install
autorecst=$?

if [ $autorecst -ne 0 ]; then
    echo ""
    echo "*** An ERROR occured on autoreconf! Check if there's a UNIX guru nearby to help you. ***"
    exit 1
fi

intltoolize --force
intltoolst=$?
if [ $intltoolst -ne 0 ]; then
    echo ""
    echo "*** An ERROR occured on intltoolize! Is it installed on your system? ***"
    exit 1
fi

echo ""
echo "*** Build system ready. ***"
echo ""

echo "        QUICK INSTALL REFERENCE:"
echo "To configure, build and install Subconvert (by default into /usr/):"
echo "  $ ./configure"
echo "  $ make"
echo "  $ sudo make install"
echo ""
echo "To install Subconvert into a different directory:"
echo "  $ ./configure --prefix=/different/dir"
echo ""
echo "To uninstall from a given prefix:"
echo "  $ make uninstall"
echo ""
echo "See ./configure --help for more info."
echo "Online Subconvert wiki: [ https://github.com/mgoral/subconvert/wiki/Installation ]"
