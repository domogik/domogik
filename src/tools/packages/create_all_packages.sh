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
# Generate all packages from sources
#
#Implements
#==========
#
#
#@author: Fritz <fritz.smh@gmail.com>
#@copyright: (C) 2007-2009 Domogik project
#@license: GPL(v3)
#@organization: Domogik

SRC_PATH="../../../"
PLG_XML_PATH="src/share/domogik/plugins/"

if [[ $# -ne 1 ]] ; then
    echo "Usage : $0 <directory>"
    echo "Create al packages in a directory"
    exit 1
fi

FOLDER=$1

for fic in $(find $SRC_PATH/$PLG_XML_PATH -name "*.xml")
  do
    plugin=$(basename $fic | sed "s/\.xml//")
    echo "********************************************************"
    echo "*    Generating package for $plugin"
    echo "********************************************************"
  
    ./pkg-mgr.py -f -c -t plugin -o $FOLDER $plugin

    #echo "Continue with next plugin ?"
    #read resp
    #if [[ $resp == "o" || $resp == "O" ]] ; then
    #    echo ""
    #else
    #    echo "Exit..."
    #    exit 0 
    #fi
done
