# -*- coding: utf-8 -*-

""" This file is part of B{Domogik} project (U{http://www.domogik.org}$

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

Plugin purpose
==============

Support Z-wave technology

Implements
==========

-Zwave

@author: Nico <nico84dev@gmail.com>
@copyright: (C) 2007-2012 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

import libopenzwave
from libopenzwave import PyManager
from collections import namedtuple
import time
from time import sleep
import os.path

FlagDebug = False # pour debug eviter recurtion +2, passé a True pour debug

OZWPLuginVers = "0.1b2"
# Déclaration de tuple nomée pour la clarification des infos des noeuds zwave (node)
# Juste à rajouter ici la déclaration pour future extension.
NamedPair = namedtuple('NamedPair', ['id', 'name'])
NodeInfo = namedtuple('NodeInfo', ['generic','basic','specific','security','version'])
GroupInfo = namedtuple('GroupInfo', ['index','label','maxAssociations','members'])

# Listes de commandes Class reconnues comme device domogik
CmdsClassAvailable = ['COMMAND_CLASS_BASIC', 'COMMAND_CLASS_SWITCH_BINARY', 'COMMAND_CLASS_SENSOR_BINARY', 
                               'COMMAND_CLASS_SENSOR_MULTILEVEL', 'COMMAND_CLASS_BATTERY']
                               
# Listes de commandes Class pour conversion des notifications NodeEvent en ValueChanged                               
CmdsClassBasicType = ['COMMAND_CLASS_SWITCH_BINARY', 'COMMAND_CLASS_SENSOR_BINARY', 'COMMAND_CLASS_SENSOR_MULTILEVEL', 
                                'COMMAND_CLASS_SWITCH_MULTILEVEL',  'COMMAND_CLASS_SWITCH_ALL',  'COMMAND_CLASS_SWITCH_TOGGLE_BINARY',  
                                'COMMAND_CLASS_SWITCH_TOGGLE_MULTILEVEL', 'COMMAND_CLASS_SENSOR_MULTILEVEL', ]

class OZwaveException(Exception):
    """"Zwave generic exception class.
    """
    def __init__(self, value):
        Exception.__init__(self)
        self.msg = "OZwave generic exception:"
        self.value = value
                                
    def __str__(self):
        return repr(self.msg+' '+self.value)
