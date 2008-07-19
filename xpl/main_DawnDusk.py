#!/usr/bin/python
# -*- encoding:utf-8 -*-

# $Author$
# $LastChangedBy$
# $LastChangedDate$
# $LastChangedRevision$

from dawndusk import DawnDusk
from xPLAPI import *
import datetime

myxpl = Manager(ip = "192.168.1.20",port = 5037, source="xpl-dawndusk.python")
mydawndusk = DawnDusk()

#Definition des paramètres
long = -1.59
lat = 48.07
fh = 1
#Attend la réception d'un message de type DAWNDUSK.REQUEST
#ATTENTION : Ce script ne respecte pas le schema DAWNDUSK.REQUEST
#Le script attend un message contenant query=day ou query=night
#Et renvoi un message du type DATETIME.BASIC avec l'heure de lever ou coucher du soleil

def dateFromTuple(tuple):
    """
    Tranforme le résultat de get_dawn_dusk en string de la forme 'yyyymmddhhmmss'
    """
    h = "%.2i" % (tuple[0] + 1) #1h en plus car en heure d'ete .TO FIX
    m = "%.2i" % (int(tuple[1]))
    s = "%.2i" % ((tuple[1] - int(tuple[1])) *  60) #Passage en seconde
    today = datetime.date.today()
    y = today.year
    mo = "%.2i" % today.month
    d = "%.2i" % today.day
    date = "%s%s%s%s%s%s" % (y, mo, d, h, m, s)
    print date
    return date
    
def getDawn(message):
    """
    Envoie un message xPL de type DATETIME.BASIC avec l'heure de lever du soleil
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
    Envoie un message xPL de type DATETIME.BASIC avec l'heure de coucher du soleil
    """
    dawn, dusk = mydawndusk.get_dawn_dusk(long, lat, fh)
    date = dateFromTuple(dusk)
    mess = Message()
    mess.set_type("xpl-stat")
    mess.set_schema("datetime.basic")
    mess.set_data_key("status",date)
    myxpl.send(mess)
   
#Listener pour le dawn
dawnL = Listener(getDawn, myxpl, {'schema':'dawndusk.request','type':'xpl-cmnd','command':'status','query':'day'})
#Listener pour le dusk
duskL = Listener(getDusk, myxpl, {'schema':'dawndusk.request','type':'xpl-cmnd','command':'status','query':'night'})
