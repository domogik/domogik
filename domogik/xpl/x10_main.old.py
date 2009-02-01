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
# $LastChangedDate: 2009-02-01 13:29:09 +0100 (dim. 01 févr. 2009) $
# $LastChangedRevision: 308 $

from x10API import *
from xPLAPI import *
from datetime import datetime

myx10 = X10API()
myxpl = Manager(ip = "192.168.1.20",port = 5036)
guirlande = ['A2','A3']
lampe = ['A1']
diff_nuit = 0 #Temps en minute avant le coucher du soleil
diff_jour = 0 #Temps en minute avant le lever du soleil
updated = False

def dawndusk(message):
    """
    Appelé à la réception d'un message de type datetime.basic
    """
    datetime = message.get_key_value(status)
    hour = datetime[8:10]
    d = datetime.today()
    da = "%.4i%.2i%.2i%.2i%.2i%.2i" % (d.year, d.month, d.day, d.hour, a.minute, a.second)
    if hour < 12:
        diff_jour = datetime - da
    else:
        diff_nuit = datetime - da
    updated = True

def x10_cb(message):
    cmd = message.get_key_value('command')
    dev = message.get_key_value('device')
    print "CMD : %s - DEV : %s" % (cmd, dev)
    if cmd.lower() == 'on':
        print myx10.on(dev)
    if cmd.lower() == 'off':
        print myx10.off(dev)

def x10_cb_porte(message):
    """
    Fonction appelée lors de l'ouverture de la porte
    """
    #TODO Ajouter un test jour / nuit
    #On demande la mise à jour des heures de lever et coucher du soleil

    if True:
        print "Ouverture détectée"
        [myx10.on(device) for device in guirlande]
        [myx10.on(device) for device in lampe]

def askUpdate():
    """
    Envoi un message pour la mise à jour des dawn & dusk time
    """
    #TODO

#Ajout du listener sur les commandes x10 classiques
general = Listener(x10_cb, myxpl, {'schema':'x10.basic','type':'xpl-cmnd'})
#Ajout du listener pour le capteur de la porte
#porte = Listener(x10_cb_porte, myxpl, {'schema':'x10.security','type':'xpl-trig','command':'alert','device':'192'})
porte = Listener(x10_cb_porte, myxpl, {'schema':'security.zone','type':'xpl-trig','zone':'x10secc0','state':'true'})
