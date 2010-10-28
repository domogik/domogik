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
#@copyright: (C) 2007-2009 Domogik project
#@license: GPL(v3)
#@organization: Domogik


if [[ $# -ne 2 ]] ; then
    echo "Usage : $0 <input directory> <repository directory>"
    echo "This script move a package from input_directory to repository and extract info.xml file to put it on repository with package name"
    exit 1
fi

INPUT=$1
OUTPUT=$2

if [[ ! -d $1 ]] ; then
    echo "<$INPUT> is not a directory"
    exit 1
fi
if [[ ! -d $2 ]] ; then
    echo "<$OUTPUT> is not a directory"
    exit 1
fi

cd $OUTPUT
for fic in $INPUT/*.tar.gz
  do
    package_name=$(basename $fic | sed "s/.tar.gz//")
    echo "==== $package_name ===="
    tar xvzf $fic info.xml
    if [[ $? -ne 0 ]] ; then
        echo "Error while processing package. Exiting..."
        exit 1
    fi
    mv info.xml $package_name.xml
    cp $fic .
    rm -f $fic
done
