#!/usr/bin/python
# -*- encoding:utf-8 -*-

# Copyright 2008 Domogik project

# This file is part of Domogik.
# Domogik is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# Domogik is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with Domogik.  If not, see <http://www.gnu.org/licenses/>.

# Author: Maxence Dunnewind <maxence@dunnewind.net>

# $LastChangedBy: maxence $
# $LastChangedDate: 2009-02-19 09:51:35 +0100 (jeu. 19 févr. 2009) $
# $LastChangedRevision: 376 $

from domogik.xpl.dawndusk import DawnDusk
from domogik.xpl.xPLAPI import *
import datetime
from domogik.common import configloader

cfgloader = Loader('dawndusk')
config = cfgloader.load()

myxpl = Manager(config["address"],port = config["port"], source = config["source"],module_name = 'dawndusk')
mydawndusk = DawnDusk()

#Parameters definitions
long = -1.59
lat = 48.07
fh = 1
#Waiting for the reception of a message of the type DAWNDUSK.REQUEST
#CAUTION : This script does not respect  DAWNDUSK.REQUEST scheme
#This script is waiting for a messgage wich contains query=day or query=night
#And return a message of the type DATETIME.BASIC with sunrise or sunset hour

def dateFromTuple(tuple):
    """
    Tranforme the result from get_dawn_dusk to string with  “yyyymmddhhmmss” form
    """
    h = "%.2i" % (tuple[0] + 1) #1h more because summer time TO FIX
    m = "%.2i" % (int(tuple[1]))
    s = "%.2i" % ((tuple[1] - int(tuple[1])) *  60) #Passage in second
    today = datetime.date.today()
    y = today.year
    mo = "%.2i" % today.month
    d = "%.2i" % today.day
    date = "%s%s%s%s%s%s" % (y, mo, d, h, m, s)
    return date
    
def getDawn(message):
    """
    Send a xPL message of the type DATETIME.BASIC with sunrise hour
    """
    dawn, dusk = mydawndusk.get_dawn_dusk(long, lat, fh)
    date = dateFromTuple(dawn)
    mess = Message()
    mess.set_type("xpl-stat")
    mess.set_schema("datetime.basic")
    mess.set_data_key("status",date)
    myxpl.send(mess)
    

def getDusk(message):
    """
    Send a xPL message of the type DATETIME.BASIC with sunset hour
    """
    dawn, dusk = mydawndusk.get_dawn_dusk(long, lat, fh)
    date = dateFromTuple(dusk)
    mess = Message()
    mess.set_type("xpl-stat")
    mess.set_schema("datetime.basic")
    mess.set_data_key("status",date)
    myxpl.send(mess)
   
#Listener for the dawn
dawnL = Listener(getDawn, myxpl, {'schema':'dawndusk.request','type':'xpl-cmnd','command':'status','query':'day'})
#Listener for the dusk
duskL = Listener(getDusk, myxpl, {'schema':'dawndusk.request','type':'xpl-cmnd','command':'status','query':'night'})
