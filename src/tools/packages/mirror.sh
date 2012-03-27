#!/bin/bash
#This file is part of B{Domogik} project (U{http://www.domogik.org}).
#
#License
#=======
#
#B{Domogik} is free software: you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.
#
#B{Domogik} is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#GNU General Public License for more details.
#
#You should have received a copy of the GNU General Public License
#along with Domogik. If not, see U{http://www.gnu.org/licenses}.
#
#Module purpose
#==============
#
# Mirror an existing repository
#
#Implements
#==========
#
#
#@author: Fritz <fritz.smh@gmail.com>
#@copyright: (C) 2007-2012 Domogik project
#@license: GPL(v3)
#@organization: Domogik


echo "This script is obsolete actually. It will be upgrader in a following release"
exit 0

TMP_PKG_LIST=/tmp/dmg-mirror-tool.lst

if [[ $# -ne 2 ]] ; then
    echo "Usage : $0 <repsitory url> <target directory>"
    echo "Mirror a repository"
    exit 1
fi

SRC=$1
DST=$2

# clean old data
rm -f $TMP_PKG_LIST

# create target folder
mkdir -p $DST

# get packages list
echo "Download package list"
wget -O $TMP_PKG_LIST $SRC/packages.lst

# copy package list file
cp $TMP_PKG_LIST $DST/packages.lst

# download each package and associated xml file
echo "Download all packages"
cd $DST
for fic in $(cat $TMP_PKG_LIST)
  do
    wget $SRC/$fic.tgz
    wget $SRC/$fic.xml
done

# clean temp data
rm -f $TMP_PKG_LIST

echo "Finished!"
