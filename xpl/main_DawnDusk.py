#!/usr/bin/python
# -*- encoding:utf-8 -*-

# $LastChangedBy: bz8 $
# $LastChangedDate: 2008-07-21 20:25:43 +0200 (lun. 21 juil. 2008) $
# $LastChangedRevision: 96 $

from dawndusk import DawnDusk
from xPLAPI import *
import datetime

myxpl = Manager(ip = "192.168.1.20",port = 5037, source="xpl-dawndusk.python")
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
    print date
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
