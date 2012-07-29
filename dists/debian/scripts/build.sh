#!/bin/bash -e

. ../libmake.sh

[ ! -z $1 ] && [ "$1" == "auto" ] && [ $(continue_auto_mode) == "n" ] && echo "domogik : Mode auto enabled but not on master architecture ... exiting ..." && exit 0

VERSION=$DMGVERSION

#PKGPARAMS="552649b6a327"
PKGPARAMS="83e0206dae2b 0.2.0-alpha1"

cd upstream/domogik
TARFILE=$(./package.sh $PKGPARAMS | grep "Final package generated :" | cut -d":" -f2)
cd ../..

mv $TARFILE .
PKGVERSION=$(echo $TARFILE | cut -d"-" -f2- | sed -e "s/.tgz//")

HGVERSION=$VERSION-`date "+%Y%m%d%H%M"`-$PKGVERSION-a

[ $(continue_update $HGVERSION ) == "n" ] && echo "domogik : Package already uploaded ... skip building ..." && exit 0

tar xvzf domogik-$PKGVERSION.tgz

rm -Rf domogik-$VERSION
rm -Rf domogik-$VERSION.orig

mv domogik-$PKGVERSION domogik-$VERSION
cp -Rf domogik-$VERSION domogik-$VERSION.orig
cp -Rf debian domogik-$VERSION

cd domogik-$VERSION

#Update changelog
OLDLANG=$LANG
FULLDATE=`export LANG="" && date "+%a, %d %b %Y %X %z"`
export LANG=$OLDLANG
cd debian
mv changelog changelog.old
mv changelog.template changelog
cat changelog.old >> changelog
sed -i -e "s/_VERSION_/$HGVERSION/" changelog
sed -i -e "s/_FULLDATE_/$FULLDATE/" changelog
cp domogik-mysql.config domogik-postgresql.config
cp domogik-mysql.templates domogik-postgresql.templates
cp domogik-primary.init domogik-secondary.init
#cp domogik-primary.default domogik-secondary.default
cp domogik-primary.cron.daily domogik-secondary.cron.daily
cd ..
#cp debian/domogik-tools.__init__.py src/tools/__init__.py
#cp debian/domogik-install.__init__.py install/__init__.py
cd ..

cd domogik-$VERSION

for patch in `find debian/patches/*`
do
    patch -p1 < $patch
done

cd ..

cp -Rf domogik-$VERSION domogik-$VERSION.orig

#exit 

cd domogik-$VERSION

dpkg-buildpackage -rfakeroot

RET=$?
#RET=1
echo ret=$RET

if [[ $RET == 0 ]]
then
	cd ..
	dupload *.changes
#	../reprepro_addchanges.sh \*.changes
	set +e
	rm *.deb
	rm *.changes
	rm *.dsc
	rm *.orig.tar.gz
	rm *.gz
	rm *.tar.gz
	rm *.tgz
	rm -Rf domogik-$VERSION
	rm -Rf domogik-$VERSION.orig
	set -e
fi
