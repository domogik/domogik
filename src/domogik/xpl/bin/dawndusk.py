#!/usr/bin/python
# -*- coding: utf-8 -*-                                                                           

""" This file is part of B{Domogik} project (U{http://www.domogik.org}).

License
=======

B{Domogik} is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

B{Domogik} is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Domogik. If not, see U{http://www.gnu.org/licenses}.

Module purpose
==============

xPL Dawndusk client

Implements
==========

- dateFromTuple(tuple)
- get_dawn(message)
- get_dusk(message)

@author: Maxence Dunnewind <maxence@dunnewind.net>
@copyright: (C) 2007-2009 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

from domogik.xpl.lib.dawndusk import DawnDusk
from domogik.xpl.lib.xplconnector import Listener
from domogik.xpl.common.xplmessage import XplMessage
import datetime
from domogik.common.configloader import Loader

#TODO : rewrite this module to use database query
cfgloader = Loader('dawndusk')
config = cfgloader.load()

myxpl = Manager(source = config["source"], module_name = 'dawndusk')
mydawndusk = DawnDusk()

#Parameters definitions
longi = -1.59
lat = 48.07
fh = 1
#Waiting for the reception of a message of the type DAWNDUSK.REQUEST
#CAUTION : This script does not respect  DAWNDUSK.REQUEST scheme
#This script is waiting for a messgage wich contains query=day or query=night
#And return a message of the type DATETIME.BASIC with sunrise or sunset hour

def dateFromTuple(tuple):
    """
    Tranforme the result from get_dawn_dusk to string with "yyyymmddhhmmss"
    form
    """
    h = "%.2i" % (tuple[0] + 1) #1h more because summer time TO FIX
    m = "%.2i" % (int(tuple[1]))
    s = "%.2i" % ((tuple[1] - int(tuple[1])) * 60) #Passage in second
    today = datetime.date.today()
    y = today.year
    mo = "%.2i" % today.month
    d = "%.2i" % today.day
    date = "%s%s%s%s%s%s" % (y, mo, d, h, m, s)
    return date


def get_dawn(message):
    """
    Send a xPL message of the type DATETIME.BASIC with sunrise hour
    """
    dawn, dusk = mydawndusk.get_dawn_dusk(longi, lat, fh)
    date = dateFromTuple(dawn)
    mess = XplMessage()
    mess.set_type("xpl-stat")
    mess.set_schema("datetime.basic")
    mess.add_data({"status" :  date})
    myxpl.send(mess)


def get_dusk(message):
    """
    Send a xPL message of the type DATETIME.BASIC with sunset hour
    """
    dawn, dusk = mydawndusk.get_dawn_dusk(longi, lat, fh)
    date = dateFromTuple(dusk)
    mess = XplMessage()
    mess.set_type("xpl-stat")
    mess.set_schema("datetime.basic")
    mess.add_data({"status" :  date})
    myxpl.send(mess)

#Listener for the dawn
dawnL = Listener(get_dawn, myxpl, {
    'schema': 'dawndusk.request',
    'xpltype': 'xpl-cmnd',
    'command': 'status',
    'query': 'day',
})
#Listener for the dusk
duskL = Listener(get_dusk, myxpl, {
    'schema': 'dawndusk.request',
    'xpltype': 'xpl-cmnd',
    'command': 'status',
    'query': 'night',
})
