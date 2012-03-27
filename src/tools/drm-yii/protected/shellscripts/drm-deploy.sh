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
# For each package in input directory, extract info.xml and put info.xml and package in repo directory
#
#Implements
#==========
#
#
#@author: Fritz <fritz.smh@gmail.com>
#@copyright: (C) 2007-2012 Domogik project
#@license: GPL(v3)
#@organization: Domogik


if [[ $# -ne 2 ]] ; then
    echo "Usage : $0 <folder> <package file>"
    echo "I a folder, this script extract info.xml file from a package and rename it"
    exit 1
fi

DIR=$1
PKG=$2

if [[ ! -f $DIR/$PKG.tgz ]] ; then
    echo "ERROR : <$DIR/$PKG.tgz> is not a file"
    exit 1
fi

cd $DIR
if [[ $? -ne 0 ]] ; then
    echo "ERROR : Folder $DIR doesn't exist"
    exit 1
fi
tar xzf $PKG.tgz info.xml
if [[ $? -ne 0 ]] ; then
    echo "ERROR : info.xml extraction failed"
    exit 1
fi
mv info.xml $PKG.xml
echo "Package deployed"
