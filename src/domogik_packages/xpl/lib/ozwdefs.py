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

OZWPLuginVers = "0.2b2"
# Déclaration de tuple nomée pour la clarification des infos des noeuds zwave (node)
# Juste à rajouter ici la déclaration pour future extension.
NamedPair = namedtuple('NamedPair', ['id', 'name'])
NodeInfo = namedtuple('NodeInfo', ['generic', 'basic', 'specific', 'security', 'version'])
GroupInfo = namedtuple('GroupInfo', ['index', 'label', 'maxAssociations', 'members'])

# Status des membres d'un group d'association pour gestion des mises à jour des nodes sleeping
MemberGrpStatus = {0: 'unknown',
                             1: 'confirmed', 
                             2: 'to confirm', 
                             3: 'to update'}
# Status des nodes dans le reseau zwave                             
NodeStatusNW = {0:'Uninitialized',
                          1:'Initialized - not known', 
                          2:'Completed',
                          3:'In progress - Devices initializing',
                          4:'In progress - Linked to controller',
                          5:'In progress - Can receive messages', 
                          6:'Out of operation', 
                          7:'In progress - Can receive messages (Not linked)'}
                            
Capabilities = ['Primary Controller', 'Secondary Controller', 'Static Update Controller', 'Bridge Controller' ,
                    'Routing', 'Listening', 'Beaming', 'Security', 'FLiRS']

# Listes de commandes Class reconnues comme device domogik
CmdsClassAvailable = ['COMMAND_CLASS_BASIC', 'COMMAND_CLASS_SWITCH_BINARY', 'COMMAND_CLASS_SENSOR_BINARY', 
                               'COMMAND_CLASS_SENSOR_MULTILEVEL', 'COMMAND_CLASS_BATTERY',  'COMMAND_CLASS_METER', 
                               'COMMAND_CLASS_SWITCH_MULTILEVEL', ]
                               
# Listes des types reconnues comme device domogik (label openzwave)
DomogikTypeAvailable = ['temperature', 'relative-humidity', 'humidity', 'battery-level', 'sensor', 'status', # sensor
                                  'power', 'energy', 'previous-reading', 'luminance',  'general', 'motion',
                                  'alarm-type', 'alarm-level', 'count', 'instant-energy-production', 'total-energy-production',
                                  'energy-production-today', 'total-production-time', 'indicator', 'locked', 'level',
                                  'operating-state', 
                                  'basic', 'switch', 'step-size', 'inc', 'dec', 'bright', 'dim',  'toggle-switch',  # Actuaror
                                  'fan-mode',  'fan-state', 'mode',  'operating-state',  'setpoint']

# Notifications reportés sur le hub xPL pour l'UI
UICtrlReportType = ['plugin-state','driver-ready',  'init-process', 'ctrl-error', 'ctrl-action',  'node-state-changed', 'value-changed']
                               
# Listes de commandes Class pour conversion des notifications NodeEvent en ValueChanged                               
CmdsClassBasicType = ['COMMAND_CLASS_SWITCH_BINARY', 'COMMAND_CLASS_SENSOR_BINARY', 'COMMAND_CLASS_SENSOR_MULTILEVEL', 
                                'COMMAND_CLASS_SWITCH_MULTILEVEL',  'COMMAND_CLASS_SWITCH_ALL',  'COMMAND_CLASS_SWITCH_TOGGLE_BINARY',  
                                'COMMAND_CLASS_SWITCH_TOGGLE_MULTILEVEL', 'COMMAND_CLASS_SENSOR_MULTILEVEL','COMMAND_CLASS_METER' ]

BasicDeviceType = {1: 'TYPE_CONTROLLER', 2: 'TYPE_STATIC_CONTROLLER', 3: 'TYPE_SLAVE', 4 :'TYPE_ROUTING_SLAVE'}
GenericDeviceType = { 0x00:'TYPE_SPECIFIC_TYPE_NOT_USED', 0x01: 'TYPE_CONTROLLER', 
                                0x02: 'TYPE_STATIC_CONTROLLER', 0x03: 'TYPE_AV_CONTROL_POINT', 
                                0x04: 'TYPE_DISPLAY',
                                0x07: 'GENERIC_TYPE_GARAGE_DOOR',
                                0x08: 'TYPE_THERMOSTAT',  0x09: 'TYPE_WINDOW_COVERING',
                                0x0f :'TYPE_REPEATER_SLAVE',  
                                0x10: 'TYPE_SWITCH_BINARY', 0x11: 'TYPE_SWITCH_MULTILEVEL', 
                                0x12: 'TYPE_REMOTE_SWITCH', 0x13: 'TYPE_SWITCH_TOGGLE',
                                0x14: 'TYPE_ZIP_GATEWAY',  
                                0x15: 'TYPE_ZIP_NODE', 
                                0xa1: 'TYPE_SENSOR_ALARM', 0x20: 'TYPE_SENSOR_BINARY', 
                                0x21: 'TYPE_SENSOR_MULTILEVEL', 0x22:'GENERIC_TYPE_WATER_CONTROL',
                                0x30: 'TYPE_METER_PULSE', 0x31: 'TYPE_METER', 
                                0x40 : 'TYPE_ENTRY_CONTROL', 0x50: 'TYPE_SEMI_INTEROPERABLE', 
                                0xff: 'TYPE_NON_INTEROPERABLE'}

SpecificDeviceType = { 0x00:{0x00:'SPECIFIC_TYPE_NOT_USED'}, 
                                0x01:{0x00:'SPECIFIC_TYPE_NOT_USED',                                #TYPE_CONTROLLER
                                         0x01:'SPECIFIC_TYPE_PORTABLE_REMOTE_CONTROLLER', 
                                         0x02:'SPECIFIC_TYPE_PORTABLE_SCENE_CONTROLLER'}, 
                                0x02:{0x00:'SPECIFIC_TYPE_NOT_USED',                               # TYPE_STATIC_CONTROLLER
                                         0x01:'SPECIFIC_TYPE_PC_CONTROLLER', 
                                         0x02:'SPECIFIC_TYPE_SCENE_CONTROLLER'}, 
                                0x03:{0x03:'SPECIFIC_TYPE_UPNP_NETWORKED'},                   # TYPE_AV_CONTROL_POINT
                                0x04:{0x00:'SPECIFIC_TYPE_NOT_USED',                              # TYPE_DISPLAY
                                         0x01:'SPECIFIC_TYPE_SIMPLE_DISPLAY'}, 
                                0x07:{0x00:'SPECIFIC_TYPE_NOT_USED',                              #  GENERIC_TYPE_GARAGE_DOOR
                                         0x01:'SPECIFIC_TYPE_SIMPLE_GARAGE_DOOR'},
                                0x08:{0x00:'SPECIFIC_TYPE_NOT_USED',                              # TYPE_THERMOSTAT
                                         0x01:'SPECIFIC_TYPE_THERMOSTAT_HEATING',
                                         0x02:'SPECIFIC_TYPE_THERMOSTAT_GENERAL'}, 
                                0x09:{0x00:'SPECIFIC_TYPE_NOT_USED',                              # TYPE_WINDOW_COVERING
                                         0x01:'SPECIFIC_TYPE_SIMPLE_WINDOW_COVERING'},  
                                0x0f :{0x00:'SPECIFIC_TYPE_NOT_USED',                             # TYPE_REPEATER_SLAVE
                                         0x01:'SPECIFIC_TYPE_REPEATER_SLAVE'}, 
                                0x10:{0x00:'SPECIFIC_TYPE_NOT_USED',                              #TYPE_SWITCH_BINARY
                                         0x01:'SPECIFIC_TYPE_POWER_SWITCH_BINARY', 
                                         0x03:'SPECIFIC_TYPE_POWER_SWITCH_BINARY_V2', 
                                         0x02:'SPECIFIC_TYPE_SCENE_SWITCH_BINARY'},                               
                                0x11:{0x00:'SPECIFIC_TYPE_NOT_USED',                             # TYPE_SWITCH_MULTILEVEL
                                         0x01:'SPECIFIC_TYPE_POWER_SWITCH_MULTILEVEL',
                                         0x03:'SPECIFIC_TYPE_MOTOR_MULTIPOSITION', 
                                         0x02:'SPECIFIC_TYPE_SCENE_SWITCH_MULTILEVEL'},     
                                0x12:{0x00:'SPECIFIC_TYPE_NOT_USED',                             # TYPE_REMOTE_SWITCH'
                                         0x04:'SPECIFIC_TYPE_SWITCH_REMOTE_TOGGLE_MULTILEVEL', 
                                         0x01:'SPECIFIC_TYPE_SWITCH_REMOTE_BINARY', 
                                         0x03:'SPECIFIC_TYPE_SWITCH_REMOTE_TOGGLE_BINARY', 
                                         0x02:'SPECIFIC_TYPE_SWITCH_REMOTE_MULTILEVEL'}, 
                                0x13:{0x00:'SPECIFIC_TYPE_NOT_USED',                             # TYPE_SWITCH_TOGGLE
                                          0x01:'SPECIFIC_TYPE_SWITCH_TOGGLE_BINARY',
                                          0x02:'SPECIFIC_TYPE_SWITCH_TOGGLE_MULTILEVEL'}, 
                                0x14:{0x00:'SPECIFIC_TYPE_NOT_USED'},                            # TYPE_ZIP_GATEWAY
                                0x15:{0x00:'SPECIFIC_TYPE_NOT_USED'},                            # TYPE_ZIP_NODE
                                0xa1:{0x00:'SPECIFIC_TYPE_NOT_USED'},                            # TYPE_SENSOR_ALARM
                                0x20:{0x00:'SPECIFIC_TYPE_NOT_USED',                             # TYPE_SENSOR_BINARY'
                                        0x01:'SPECIFIC_TYPE_ROUTING_SENSOR_BINARY'}, 
                                0x21:{0x00:'SPECIFIC_TYPE_NOT_USED',                              # TYPE_SENSOR_MULTILEVEL
                                         0x01:'SPECIFIC_TYPE_ROUTING_SENSOR_MULTILEVEL',
                                         0x02:'SPECIFIC_TYPE_CHIMNEY_FAN_SENSOR_MULTILEVEL'}, 
                                0x22:{0x00:'SPECIFIC_TYPE_NOT_USED',                              # GENERIC_TYPE_WATER_CONTROL
                                         0x01:'SPECIFIC_TYPE_POWER_SHOWER'},
                                0x30:{0x00:'SPECIFIC_TYPE_NOT_USED'},                             #  TYPE_METER_PULSE
                                0x31:{0x00:'SPECIFIC_TYPE_NOT_USED'},                             # TYPE_METER
                                
                                0x40:{0x00:'SPECIFIC_TYPE_NOT_USED',                             # TYPE_ENTRY_CONTROL
                                         0x01:'SPECIFIC_TYPE_DOOR_LOCK'}, 
                                0x50:{0x00:'SPECIFIC_TYPE_NOT_USED',                             # TYPE_SEMI_INTEROPERABLE
                                         0x01:'SPECIFIC_TYPE_ENERGY_PRODUCTION'},
                                0xff: {0x00:'SPECIFIC_TYPE_NOT_USED'}                             # TYPE_NON_INTEROPERABLE
                                }

class OZwaveException(Exception):
    """"Zwave generic exception class.
    """
    def __init__(self, value):
        Exception.__init__(self)
        self.msg = "OZwave generic exception:"
        self.value = value
                                
    def __str__(self):
        return repr(self.msg+' '+self.value)
