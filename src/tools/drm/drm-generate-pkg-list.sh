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
# This script generates package list
#
#Implements
#==========
#
#
#@author: Fritz <fritz.smh@gmail.com>
#@copyright: (C) 2007-2009 Domogik project
#@license: GPL(v3)
#@organization: Domogik


TMP_DIR=/tmp/domogik-repo
FILENAME=packages.lst

if [[ $# -ne 1 ]] ; then
    echo "Usage : $0 <repository>"
    echo "For each package in repository, generate package list"
    exit 1
fi

FOLDER=$1

mkdir -p $TMP_DIR
if [[ $? -ne 0 ]] ; then
    echo "Error while creating temporary directory <$TMP_DIR>"
    exit 1
fi

if [[ ! -d $1 ]] ; then
    echo "<$INPUT> is not a directory"
    exit 1
fi

rm -f $TMP_DIR/FILENAME
if [[ $? -ne 0 ]] ; then
    echo "Could not delete file $TMP_DIR/$FILENAME"
    exit 1
fi

echo "Domogik repository" > $TMP_DIR/$FILENAME
if [[ $? -ne 0 ]] ; then
    echo "Could not write in file $TMP_DIR/$FILENAME"
    exit 1
fi

cd $FOLDER
for fic in $FOLDER/*.xml
  do
    if [[ -f $fic ]] ; then
        package_name=$(basename $fic | sed "s/.xml//")
        echo "- $package_name"
        echo $package_name >> $TMP_DIR/$FILENAME
        if [[ $? -ne 0 ]] ; then
            echo "Could not write in file $TMP_DIR/$FILENAME"
            exit 1
        fi
    fi
done

mv $TMP_DIR/$FILENAME $FOLDER
if [[ $? -ne 0 ]] ; then
    echo "Could not move file $TMP_DIR/$FILENAME to $FOLDER"
    exit 1
fi

echo "Packages.lst file generated"
