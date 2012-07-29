#!/bin/bash

. ../libmake.sh

[ ! -z $1 ] && [ "$1" == "auto" ] && [ $(continue_auto_mode) == "n" ] && echo "domogik : Mode auto enabled but not on master architecture ... exiting ..." && exit 0

VERSION=$DMGVERSION

set -e

[ ! -d upstream ] && mkdir upstream
cd upstream
if [[ -d domogik ]]
then
    cd domogik
    hg pull
    hg update 0.2
    cd ..
else
    hg clone http://hg.domogik.org/domogik/
fi

#rm -Rf domogik-$VERSION
#cp -Rf domogik domogik-$VERSION
#cd domogik-$VERSION
#find . -depth -name ".hg" -exec rm -rf {} \;
#find . -depth -name ".hgignore" -exec rm -f {} \;
#cd ..

#tar czf domogik_$VERSION.hg.tar.gz domogik-$VERSION

#mv domogik_$VERSION.hg.tar.gz ../

#tar cf domogik_$VERSION.install.hg.tar \
#    --exclude=src/domogik/ui \
#   --exclude=src/domogik/xpl \
#   --exclude=src/external \
#   --exclude=src/share/domogik \
#   domogik-$VERSION
#
#tar rf domogik_$VERSION.install.hg.tar \
#   domogik-$VERSION/src/domogik/ui/__init__.py \
#   domogik-$VERSION/src/domogik/xpl/__init__.py \
#   domogik-$VERSION/src/domogik/xpl/bin/__init__.py \
#   domogik-$VERSION/src/domogik/xpl/bin/dbmgr.py \
#   domogik-$VERSION/src/domogik/xpl/bin/dump_xpl.py \
#   domogik-$VERSION/src/domogik/xpl/bin/manager.py \
#   domogik-$VERSION/src/domogik/xpl/bin/pkgmgr.py \
#   domogik-$VERSION/src/domogik/xpl/bin/rest.py \
#   domogik-$VERSION/src/domogik/xpl/bin/send.py \
#   domogik-$VERSION/src/domogik/xpl/bin/version.py \
#   domogik-$VERSION/src/domogik/xpl/common \
#   domogik-$VERSION/src/domogik/xpl/helpers/__init__.py \
#   domogik-$VERSION/src/domogik/xpl/lib/__init__.py \
#   domogik-$VERSION/src/domogik/xpl/lib/rest \
#   domogik-$VERSION/src/domogik/xpl/tools \
#   domogik-$VERSION/src/share/domogik/scenarios
#
#rm -Rf domogik-$VERSION
#
#mv domogik_$VERSION.install.hg.tar ../
