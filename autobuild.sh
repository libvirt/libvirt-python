#!/bin/sh

set -ve

: ${AUTOBUILD_INSTALL_ROOT="$HOME/builder"}

rm -rf MANIFEST dist build


python setup.py sdist

python setup.py build
python setup.py test
python setup.py install --root="$AUTOBUILD_INSTALL_ROOT"

type -p /usr/bin/rpmbuild > /dev/null 2>&1 || exit 0

if [ -n "$AUTOBUILD_COUNTER" ]; then
    EXTRA_RELEASE=".auto$AUTOBUILD_COUNTER"
else
    NOW=`date +"%s"`
    EXTRA_RELEASE=".$USER$NOW"
fi
rpmbuild --nodeps --define "extra_release $EXTRA_RELEASE" -ta --clean dist/*.tar.gz
