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

from ozwdefs import *
import binascii
import libopenzwave
from libopenzwave import PyManager
import time
from time import sleep
import os.path


class OZwaveValueException(OZwaveException):
    """"Zwave ValueNode exception class"""
            
    def __init__(self, value):
        OZwaveException.__init__(self, value)
        self.msg = "OZwave Value exception:"


class ZWaveValueNode:
    """ Représente une des valeurs du node """
    def __init__(self, homeId, nodeId, valueData):
        '''
        Initialise la valeur du node
        @param homeid: ID du réseaux home/controleur
        @param nodeid: ID du node
        @param valueData: valueId dict (voir libopenzwave.pyx)
            ['valueId'] = {
                    'homeId' : uint32, # Id du réseaux
                    'nodeId' : uint8,   # Numéro du noeud
                    'commandClass' : PyManager.COMMAND_CLASS_DESC[v.GetCommandClassId()], # Liste des cmd CLASS reconnues
                    'instance' : uint8  # numéro d'instance de la value 
                    'index' : uint8 # index de classement de la value
                    'id' : uint64 # Id pointeur C++ de la value
                    'genre' : enum ValueGenre:   # Type de data OZW
                                ValueGenre_Basic = 0
                                ValueGenre_User = 1
                                ValueGenre_Config = 2
                                ValueGenre_System = 3
                                ValueGenre_Count = 4
                    'type' : enum ValueType:  # Type de données
                                ValueType_Bool = 0
                                ValueType_Byte = 1
                                ValueType_Decimal = 2
                                ValueType_Int = 3
                                ValueType_List = 4
                                ValueType_Schedule = 5
                                ValueType_Short = 6
                                ValueType_String = 7
                                ValueType_Button = 8
                                ValueType_Max = ValueType_Button
                                
                    'value' : str,      # Valeur même
                    'label' : str,      # Nom de la value OZW
                    'units' : str,      # unité
                    'readOnly': manager.IsValueReadOnly(v),  # Type d'accès lecture/ecriture
                    }   
        '''
        self._homeId = homeId
        self._nodeId = nodeId
        self._valueData = valueData
        self._lastUpdate = None
        
    # On accède aux attributs uniquement depuis les property
  
    homeId = property(lambda self: self._homeId)
    nodeId = property(lambda self: self._nodeId)
    lastUpdate = property(lambda self: self._lastUpdate)
    valueData = property(lambda self: self._valueData)

    def getValue(self, key):
        """Retourne la valeur du dict valueData correspondant à key"""
        return self.valueData[key] if self._valueData.has_key(key) else None
    
    def update(self, args):
        """Mise à jour de valueData depuis les arguments du callback """
        self._valueData = args['valueId']
        self._lastUpdate = time.time()

    def getInfos(self):
        """ Retourne les informations de la value , format dict{} """
        retval={}
        retval = self.valueData
        retval['homeId'] = int(retval['homeId']) # Pour etre compatible avec javascript
        retval['id'] = int(retval['id']) # Pour etre compatible avec javascript
        retval['domogikdevice']  = True if (retval['commandClass'] in  CmdsClassAvailable) else False
        return retval
        
    def valueToxPLTrig(self, msgtrig):
        """Renvoi le message xPL à trigger en fonction de la command_class de la value
        @param mstrig: Dict avec les infos générales déja renseignées
        """
        # TODO: Traiter le formattage en fonction du type de message à envoyer à domogik rajouter ici le traitement pour chaque command_class
        # ne pas modifier celles qui fonctionnent mais rajouter. la fusion ce fera après implémentation des toutes les command-class.
        sendxPL = False
        if self.valueData['commandClass'] == 'COMMAND_CLASS_BASIC' :
            sendxPL = True
            if self.valueData['readOnly'] :
                msgtrig['genre'] = 'sensor'
                msgtrig['schema'] ='sensor.basic'
            else : 
                msgtrig['genre'] = 'actuator'
                msgtrig['schema'] ='ozwave.basic'
            msgtrig['level']=  self.valueData['value']
        if self.valueData['commandClass'] == 'COMMAND_CLASS_SWITCH_BINARY' :
            if self.valueData['type'] == 'Bool' :
                sendxPL = True
                msgtrig['schema'] ='ozwave.basic'
                msgtrig['genre'] = 'actuator'
                msgtrig['level']=  self.valueData['value']
        elif self.valueData['commandClass'] == 'COMMAND_CLASS_SENSOR_BINARY' : 
            if self.valueData['type'] == 'Bool' :
                sendxPL = True
                msgtrig['schema'] ='sensor.basic'
                msgtrig ['genre'] = 'sensor'
                msgtrig ['type'] = 'status'
                msgtrig ['value'] = self.valueData['value']
        elif self.valueData['commandClass'] == 'COMMAND_CLASS_SENSOR_MULTILEVEL' :
                sendxPL = True
                msgtrig['schema'] ='sensor.basic'
                msgtrig ['genre'] = 'sensor'
                msgtrig ['value'] = self.valueData['value']
                msgtrig ['type'] = self.valueData['label'].lower()
                msgtrig ['units']= self.valueData['units']
        elif self.valueData['commandClass'] == 'COMMAND_CLASS_BATTERY' :
                sendxPL = True
                msgtrig['schema'] ='sensor.basic'
                msgtrig ['genre'] = 'sensor'
                msgtrig ['value'] = self.valueData['value']
                msgtrig ['units']= self.valueData['units']
        if sendxPL :
            return msgtrig
        else : return None
       
    def __str__(self):
        return 'homeId: [{0}]  nodeId: [{1}]  valueData: {2}'.format(self._homeId, self._nodeId, self._valueData)
