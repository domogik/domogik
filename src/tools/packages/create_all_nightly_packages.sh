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
# Generate all nightly packages from sources
#
#Implements
#==========
#
#
#@author: Fritz <fritz.smh@gmail.com>
#@copyright: (C) 2007-2012 Domogik project
#@license: GPL(v3)
#@organization: Domogik

SRC_PATH="../../../"
PKGMGR="../../domogik/xpl/bin/pkgmgr.py"
PLG_JSON_PATH="src/share/domogik/plugins/"
EXT_JSON_PATH="src/share/domogik/externals/"

if [[ $# -ne 1 ]] ; then
    echo "Usage : $0 <directory>"
    echo "Create al packages in a directory"
    exit 1
fi

FOLDER=$1
mkdir -p ${FOLDER}

for fic in $(find ${SRC_PATH}/${PLG_JSON_PATH} -name "*.json")
  do
    plugin=$(basename ${fic} | sed "s/\.json//")
    echo "********************************************************"
    echo "*    Generating package for plugin $plugin"
    echo "********************************************************"
  
    ${PKGMGR} -n ${fic}
    ${PKGMGR} -f -c -t plugin -o ${FOLDER} ${plugin}
done

for fic in $(find ${SRC_PATH}/${EXT_JSON_PATH} -name "*.json")
  do
    external=$(basename ${fic} | sed "s/\.json//")
    echo "********************************************************"
    echo "*    Generating package for external member $external"
    echo "********************************************************"
  
    ${PKGMGR} -n ${fic}
    ${PKGMGR} -f -c -t external -o ${FOLDER} ${external}
done
