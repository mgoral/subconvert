#!/bin/sh

# Very simple version generator
# First, we'll check for .tarball-version file (present only in dist tarballs). If it exists, we'll
# take version number from there.  Second, we'll try to create git-based version and use it. If all
# methods above fail, we'll set some kind of fallback version number.
#
# Version number is changed in subconvert/utils/version.py every time make is invoked, so
# Subconvert will always display a proper version number. It's a little hacky, but it works.

VERSION_FILE=".tarball-version"
VERSION=""
FALLBACK="1.x-unknown"

nl='
'

if [ -f $VERSION_FILE ]; then
    VERSION=`cat $VERSION_FILE` || VERSION=""
fi

if [ "$VERSION" = "" ]; then
    if [ -d .git ]; then
        VERSION=`git describe --abbrev=4 --dirty --always --tags`
    fi
fi

if [ "$VERSION" = "" ]; then
    VERSION=$FALLBACK
fi

echo $VERSION | tr -d "$nl"
