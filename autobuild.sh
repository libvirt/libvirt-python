#!/bin/sh

set -ve

: ${AUTOBUILD_INSTALL_ROOT="$HOME/builder"}

rm -rf MANIFEST dist build


python2 setup.py sdist

python2 setup.py build
python2 setup.py test
python2 setup.py install --root="$AUTOBUILD_INSTALL_ROOT"

if test -f /usr/bin/python3 ; then
  python3 setup.py build
  python3 setup.py test
  python3 setup.py install --root="$AUTOBUILD_INSTALL_ROOT"
fi

type -p /usr/bin/rpmbuild > /dev/null 2>&1 || exit 0

if [ -n "$AUTOBUILD_COUNTER" ]; then
    EXTRA_RELEASE=".auto$AUTOBUILD_COUNTER"
else
    NOW=`date +"%s"`
    EXTRA_RELEASE=".$USER$NOW"
fi
rpmbuild --nodeps --define "extra_release $EXTRA_RELEASE" -ta --clean dist/*.tar.gz
