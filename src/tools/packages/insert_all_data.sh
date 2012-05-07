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
# Insert data for all plugins in database
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
PLG_XML_PATH="src/share/domogik/plugins/"
HARD_XML_PATH="src/share/domogik/externals/"
CUR_DIR=`pwd`
FULL_PATH=$0
PROG_NAME=${FULL_PATH##*/}
APP_DIR=${FULL_PATH%%$PROG_NAME}
cd $APP_DIR
for fic in $SRC_PATH/$PLG_XML_PATH/*xml
do
    ./insert_data.py $fic
done
for fic in $SRC_PATH/$HARD_XML_PATH/*xml
do
    ./insert_data.py $fic
done
cd $CUR_DIR
