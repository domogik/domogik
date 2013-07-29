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
    def __init__(self, node, valueData):
        '''
        Initialise la valeur du node
        @param node: ZWaveNode node 'parent'
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
        self._node = node
        self._valueData = valueData
        self._lastUpdate = time.time()
        self._tempConv = True # Conversion forcée de F en °C, a mettre en option.
        
    # On accède aux attributs uniquement depuis les property
  
    homeId = property(lambda self: self._node._homeId)
    nodeId = property(lambda self: self._node._nodeId)
    lastUpdate = property(lambda self: self._lastUpdate)
    valueData = property(lambda self: self._valueData)
    labelDomogik = property(lambda self: self._getLabelDomogik())
    isPolled = property(lambda self:self._node._manager.isPolled(self.valueData['id']))
    
    def getMemoryUsage(self):
        """Renvoi l'utilisation memoire de la value en octets"""
        return sys.getsizeof(self) + sum(sys.getsizeof(v) for v in self.__dict__.values())
        
    def getValue(self, key):
        """Retourne la valeur du dict valueData correspondant à key"""
        return self.valueData[key] if self._valueData.has_key(key) else None
    
    def getOZWValue(self):
        """Retourne la valeur réelle lut par openzwave"""
        if self.valueData['genre'] != 'Config' :
            retval = self._node._manager.getValue(self.valueData['id'])
            self._valueData['value'] = retval
            self._lastUpdate = time.time()
            return retval
        else :
            print "getOZWValue : call requestConfigParam waiting ValueChanged..."
            self._node._manager.requestConfigParam(self.homeId,  self.nodeId,  self.valueData['index'])
            return self._valueData['value'] 
        
    def setValue(self, val):
        """Envois sur le réseau zwave le 'changement' de valeur à la valueNode
            Retourne un dict {
                value : valeur envoyée
                error : texte de l'erreur éventuelle }
        """
        print type (val)
        button = False
        retval = {'value': False,  'error':  '' }
        if self.valueData['genre'] != 'Config' or self.valueData['type'] == 'List' : # TODO: Pas encore de gestion d'une config en type list, force envoie par setvalue
            if self.valueData['type'] == 'Bool':
                value = False if val in [False, 'FALSE', 'False',  'false', '',  0,  0.0, (),  [],  {},  None ] else True
                v = bool(val)
                print type(value), value,   "----",  type(v),  v
            elif self.valueData['type'] == 'Byte' : value = int(val)
            elif self.valueData['type'] == 'Decimal' : value = float(val)
            elif self.valueData['type'] == 'Int' : value = int(val)
            elif self.valueData['type'] == 'List' : value = str(val)
            elif self.valueData['type'] == 'Schedule' : value = int(val)  # TODO: Corriger le type schedule dans setvalue
            elif self.valueData['type'] == 'Short' : value = long(val)
            elif self.valueData['type'] == 'String' : value = str(val)
            elif self.valueData['type'] == 'Button' : # TODO: type button set value ?
                button = True
                value = bool(val)
                retval ['value']   = val
                print "--Gestion du type button"
                if val :
                    ret = self._node._manager.pressButton(self.valueData['id'])
                    print "type button , presscommand :",  val
                else :
                    ret = self._node._manager.releaseButton(self.valueData['id'])
                    print "type button , releasecommand :",  val
                if not ret :
                    retval ['error']   = 'Value is not a Value Type_Button.'
            else : value = val        
            print ("setValue de ", self.valueData['commandClass'], " instance :", self.valueData['instance'], " value : ",  value,
                       " on valueId :" , self.valueData['id'], " type : ",  self.valueData['type'])       
            if not button :
                if not self._node._manager.setValue(self.valueData['id'], value)  : 
                    self._node._ozwmanager._log.error ("setValue return bad type : %s, instance :%d, value : %s, on valueId : %d" %(self.valueData['commandClass'], self.valueData['instance'],  val, self.valueData['id']))
                    print("return bad type value")
                    retval ['value'] = False
                    retval['error'] = "Return bad type value."
                else : 
                    self._valueData['value'] = val
                    self._lastUpdate = time.time()
                    retval ['value'] = val
        else :
            if not self._node._manager.setConfigParam(self.homeId,  self.nodeId,  self.valueData['index'], int(val))  :
                self._node._ozwmanager._log.error ("setConfigParam no send message : %s, index :%d, value : %s, on valueId : %d" %(self.valueData['commandClass'], self.valueData['index'],  val, self.valueData['id']))
                print("setConfigParam : no send message")
                retval ['value'] = False
                retval['error'] = "setConfigParam : no send message."
            else : 
                self._valueData['value'] = val
                self._lastUpdate = time.time()
                retval ['value'] = val
        if self.valueData['genre'] == 'Config' :
            self._node._manager.requestConfigParam(self.homeId,  self.nodeId,  self.valueData['index'])
            print "setValue : call requestConfigParam..."
        return retval
            
    def updateData(self, valueData):
        """Mise à jour de valueData depuis les arguments du callback."""
        if self._tempConv and valueData['label'].lower() == 'temperature' and valueData['units'] == 'F': # TODO: Conversion forcée de F en °C, a mettre en option.
            valueData['units'] = '°C'
            print '************** Convertion : ',  float(valueData['value'])
            print float(valueData['value'])*(5.0/9)
            valueData['value'] = (float(valueData['value'])*(5.0/9))-(160.0/9)
            print valueData['value']

        self._valueData = dict(valueData)
        self._lastUpdate = time.time()
        valueData['homeId'] = int(valueData['homeId']) # Pour etre compatible avec javascript
        valueData['id'] = str(valueData['id']) # Pour etre compatible avec javascript
        self._node.reportToUI({'notifytype': 'value-changed', 'usermsg' :'Value has changed.', 'data': valueData})

    def convertInType(self,  val):
        """Convertion de val dans le type de la value."""
        retval = val
        valT = type(val)
        selfT = type(self._valueData['value'])
        if valT in [int , long, float, complex, bool] :
            if selfT == bool : retval = bool(val)
            elif selfT == int : retval = int(val)
            elif selfT == long : retval = long(val)
            elif selfT == float : retval = float(val)
            elif selfT == complex : retval = complex(val)                    
        elif  valT == str :
            if selfT == bool :
                Cval = val.capitalize()
                retval = True if Cval in ['', 'True',  'T',  'Yes',  'Y'] else False
            elif selfT == int : retval = int(val)
            elif selfT == long : retval = long(val)
            elif selfT == float : retval = float(val)
            elif selfT == complex : retval = complex(val)
        return retval
            
    def _getLabelDomogik(self):
        """ retourne le label OZW formaté pour les listener domogik, en lowcase et espaces remplacés pas '-',
            pour compatibilité adresse web et appel rest (spec Xpl)."""
        return self.valueData['label'].lower().replace(" ", "-")
        
    def getDomogikDevice(self):
        """Determine si la value peut être un device domogik et retourne le format du nom de device"""
        if (self.valueData['commandClass'] in  CmdsClassAvailable) and (self.labelDomogik in  DomogikTypeAvailable) :
            nameAssoc = self._node._ozwmanager._nameAssoc
            retval = "%s.%d.%d" % (nameAssoc.keys()[nameAssoc.values().index(self.valueData['homeId'])] , self._node.nodeId, self.valueData['instance'])        
        else: retval = ""
        return retval

    def getInfos(self):
        """ Retourne les informations de la value , format dict{} """
        retval = {}
        retval = dict(self.valueData)
        retval['homeId'] = int(retval['homeId']) # Pour etre compatible avec javascript
        retval['id'] = str(retval['id']) # Pour etre compatible avec javascript
        retval['domogikdevice']  = self.getDomogikDevice()
        retval['help'] = self.getHelp()
        retval['polled'] = self.isPolled
        retval['pollintensity'] = self.getPollIntensity()
        retval['listElems'] = list(self.getListItems()) if (self.valueData['type'] == 'List')  else None
        return retval
    
    def getValueItemStr(self):
        """Retourne la string selectionnée dans la liste des valeurs possible pour le type list"""
        retval = ""
        if self.valueData['type'] == 'List':
            retval = self._node._manager.getValueListSelectionStr(self.valueData['id'])           
        return retval
        
    def getValueItemNum(self):
        """Retourne la string selectionnée dans la liste des valeurs possible pour le type list"""
        retval = None
        if self.valueData['type'] == 'List':
            retval = self._node._manager.getValueListSelectionNum(self.valueData['id'])           
        return retval
          
    def getListItems(self):
        """Retourne la liste des valeurs possible pour le type list"""
        retval = set()
        if self.valueData['type'] == 'List':
            retval = self._node._manager.getValueListItems(self.valueData['id'])           
        return retval
        
    def getHelp(self):
        """Retourne l'aide utilisateur concernant la fonctionnalité du device"""
        return self._node._manager.getValueHelp(self.valueData['id'])
        
    def enablePoll(self, intensity = 1):    
        """Enable the polling of a device's state.

            :param id: The ID of the value to start polling
            :type id: int
            :param intensity: The intensity of the poll
            :type intensity: int
            :return: True if polling was enabled.
            :rtype: bool"""
        try :
            intensity = int(intensity)
        except Exception as e:
            self._log.error('value.enablePoll(intensity) :' + e.message)
            return {"error" : "Enable poll, error : %s" %e.message}
        return self._node._manager.enablePoll(self.valueData['id'], intensity)
        
    def disablePoll(self):
        """Disable polling of a value.

            :param id: The ID of the value to disable polling.
            :type id: int
            :return: True if polling was disabled.
            :rtype: bool """
        return self._node._manager.disablePoll(self.valueData['id'])
           
    def getPollIntensity(self):
        """Get the intensity with which this value is polled (0=none, 1=every time through the list, 2-every other time, etc).
            :param id: The ID of a value.
            :type id: int
            :return: A integer containing the poll intensity
            :rtype: int"""
        #TODO: A réactiver dans la libopenzwave.pyx
        return self._node._manager.getPollIntensity(self.valueData['id'])

    def setPollIntensity(self, intensity):
        """Set the frequency of polling (0=none, 1=every time through the set, 2-every other time, etc)

            :param id: The ID of the value whose intensity should be set
            :type id: int
            :param intensity: the intensity of the poll
            :type intensity: int
            :return: True if polling is active.
            :rtype: bool"""
        return self._node._manager.setPollIntensity(self.valueData['id'], intensity)
    
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
                msgtrig['schema'] = 'sensor.basic'
            else : 
                msgtrig['genre'] = 'actuator'
                msgtrig['schema'] = 'ozwave.basic'
            msgtrig['level'] =  self.valueData['value']
        if self.valueData['commandClass'] == 'COMMAND_CLASS_SWITCH_BINARY' :
            if self.valueData['type'] == 'Bool' :
                sendxPL = True
                msgtrig['schema'] = 'ozwave.basic'
                msgtrig['genre'] = 'actuator'
                msgtrig['level'] =  self.valueData['value']
        elif self.valueData['commandClass'] == 'COMMAND_CLASS_SWITCH_MULTILEVEL' :
            sendxPL = True
            if self.valueData['readOnly'] :
                msgtrig['genre'] = 'sensor'
                msgtrig['schema'] = 'sensor.basic'
            else : 
                msgtrig['genre'] = 'actuator'
                msgtrig['schema'] = 'ozwave.basic'
            msgtrig['level'] =  self.valueData['value']
        elif self.valueData['commandClass'] == 'COMMAND_CLASS_SENSOR_BINARY' : 
            if self.valueData['type'] == 'Bool' :
                sendxPL = True
                msgtrig['schema'] = 'sensor.basic'
                msgtrig ['genre'] = 'sensor'
                msgtrig ['type'] = 'status'
                msgtrig ['value'] = self.valueData['value']
        elif self.valueData['commandClass'] == 'COMMAND_CLASS_SENSOR_MULTILEVEL' :
            sendxPL = True
            msgtrig['schema'] = 'sensor.basic'
            msgtrig ['genre'] = 'sensor'
            if self.valueData['type'] ==  'Decimal' :   #TODO: A supprimer quand Widget gerera les digits.
                msgtrig['value'] = round(self.valueData['value'], 2)
            else:
                msgtrig ['value'] = self.valueData['value']
            msgtrig ['type'] = self.labelDomogik
            msgtrig ['units'] = self.valueData['units']
        elif self.valueData['commandClass'] == 'COMMAND_CLASS_BATTERY' :
            sendxPL = True
            msgtrig['schema'] = 'sensor.basic'
            msgtrig ['genre'] = 'sensor'
            msgtrig ['value'] = self.valueData['value']
            msgtrig ['units'] = self.valueData['units']
        elif self.valueData['commandClass'] == 'COMMAND_CLASS_METER' :
            sendxPL = True
            msgtrig['schema'] = 'sensor.basic'
            msgtrig ['genre'] = 'sensor'
            msgtrig ['type'] = self.labelDomogik
            if self.valueData['type'] ==  'Decimal' :   #TODO: A supprimer quand Widget gerera les digits.
                msgtrig['value'] = round(self.valueData['value'], 2)
            else:
                msgtrig ['value'] = self.valueData['value']
            msgtrig ['units'] = self.valueData['units']

        msgtrig ['type'] = self.labelDomogik  #TODO: supprimer les autres msgtrig ['type'] si placé ici est OK
    
        if sendxPL :
            return msgtrig
        else : return None
       
    def __str__(self):
        return 'homeId: [{0}]  nodeId: [{1}]  valueData: {2}'.format(self.homeId, self.nodeId, self.valueData)
