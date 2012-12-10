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

import binascii
import libopenzwave
from libopenzwave import PyManager
from ozwvalue import ZWaveValueNode
from ozwdefs import *
import time
from time import sleep

class OZwaveNodeException(OZwaveException):
    """"Zwave Node exception class"""
            
    def __init__(self, value):
        OZwaveException.__init__(self, value)
        self.msg = "OZwave Node exception:"

class ZWaveNode:
    '''Représente un device (node) inclu dans le réseau Z-Wave'''

    def __init__(self, ozwmanager,  homeId, nodeId):
        '''initialise le node zwave
        @param manger: pointeur sur l'instance du manager
        @param homeid: ID du réseaux home/controleur
        @param nodeid: ID du node
        '''
        self._ozwmanager = ozwmanager
        self._manager = ozwmanager._manager
        self._lastUpdate = None
        self._homeId = homeId
        self._nodeId = nodeId
        self._capabilities = set()
        self._commandClasses = set()
        self._neighbors = set()
        self._nodeInfos = None
        self._values = dict()  # voir la class ZWaveValueNode
        self._name = ''
        self._location = ''
        self._manufacturer = None
        self._product = None
        self._productType = None
        self._groups = list()
        self._sleeping = True
        
    # On accède aux attributs uniquement depuis les property
    # Chaque attribut est une propriétée qui est automatique à jour au besoin via le réseaux Zwave
    id = property(lambda self: self._nodeId)
    name = property(lambda self: self._name)
    location = property(lambda self: self._location)
    product = property(lambda self: self._product.name if self._product else '')
    productType = property(lambda self: self._productType.name if self._productType else '')
    lastUpdate = property(lambda self: self._lastUpdate)
    homeId = property(lambda self: self._homeId)
    nodeId = property(lambda self: self._nodeId)
    capabilities = property(lambda self: ', '.join(self._capabilities))
    commandClasses = property(lambda self: self._commandClasses)
    neighbors = property(lambda self:self._neighbors)
    values = property(lambda self:self._values)
    manufacturer = property(lambda self: self._manufacturer.name if self._manufacturer else '')
    groups = property(lambda self:self._groups)
    isSleeping = property(lambda self: self._isSleeping())
    isLocked = property(lambda self: self._getIsLocked())
    level = property(lambda self: self._getLevel())
    isOn = property(lambda self: self._getIsOn())
    batteryLevel = property(lambda self: self._getBatteryLevel())
    signalStrength = property(lambda self: self._getSignalStrength())
    basic = property(lambda self:  BasicDeviceType[self._nodeInfos.basic] if self._nodeInfos else None)
    generic = property(lambda self:  GenericDeviceType[self._nodeInfos.generic] if self._nodeInfos else None)
    specific = property(lambda self:  SpecificDeviceType[self._nodeInfos.generic][self._nodeInfos.specific] if self._nodeInfos else None)
    security = property(lambda self: self._nodeInfos.security if self._nodeInfos else None)
    version = property(lambda self:  self._nodeInfos.version if self._nodeInfos else None)

    def _getIsLocked(self):
        return False
    
    def _getGroupsDict(self):
        """Retourne les définitions de groups sous forme de dict"""
        grps = []
        print('Get groups dict')
        for grp in self.groups :
            group = {}
            group['index'] = grp.index
            group['label'] = grp.label
            group['maxAssociations'] = grp.maxAssociations
            group['members'] = []
            for m in grp.members:
                mbr={}
                mbr['id']=m
                mbr['status']=grp.members[m]
                group['members'].append(mbr)
                print group
            grps.append(group)
        return grps
        
# Fonction de renvoie des valeurs des valueNode en fonction des Cmd CLASS zwave
# C'est ici qu'il faut enrichire la prise en compte des fonctions Zwave
# COMMAND_CLASS implémentées :

#        0x26: 'COMMAND_CLASS_SWITCH_MULTILEVEL',
#        0x80: 'COMMAND_CLASS_BATTERY',
#        0x25: 'COMMAND_CLASS_SWITCH_BINARY',
#        0x20: 'COMMAND_CLASS_BASIC',


# TODO:

#        0x00: 'COMMAND_CLASS_NO_OPERATION',

#        0x21: 'COMMAND_CLASS_CONTROLLER_REPLICATION',
#        0x22: 'COMMAND_CLASS_APPLICATION_STATUS',
#        0x23: 'COMMAND_CLASS_ZIP_SERVICES',
#        0x24: 'COMMAND_CLASS_ZIP_SERVER',
#        0x27: 'COMMAND_CLASS_SWITCH_ALL',
#        0x28: 'COMMAND_CLASS_SWITCH_TOGGLE_BINARY',
#        0x29: 'COMMAND_CLASS_SWITCH_TOGGLE_MULTILEVEL',
#        0x2A: 'COMMAND_CLASS_CHIMNEY_FAN',
#        0x2B: 'COMMAND_CLASS_SCENE_ACTIVATION',
#        0x2C: 'COMMAND_CLASS_SCENE_ACTUATOR_CONF',
#        0x2D: 'COMMAND_CLASS_SCENE_CONTROLLER_CONF',
#        0x2E: 'COMMAND_CLASS_ZIP_CLIENT',
#        0x2F: 'COMMAND_CLASS_ZIP_ADV_SERVICES',
#        0x30: 'COMMAND_CLASS_SENSOR_BINARY',
#        0x31: 'COMMAND_CLASS_SENSOR_MULTILEVEL',
#        0x32: 'COMMAND_CLASS_METER',
#        0x33: 'COMMAND_CLASS_ZIP_ADV_SERVER',
#        0x34: 'COMMAND_CLASS_ZIP_ADV_CLIENT',
#        0x35: 'COMMAND_CLASS_METER_PULSE',
#        0x3C: 'COMMAND_CLASS_METER_TBL_CONFIG',
#        0x3D: 'COMMAND_CLASS_METER_TBL_MONITOR',
#        0x3E: 'COMMAND_CLASS_METER_TBL_PUSH',
#        0x38: 'COMMAND_CLASS_THERMOSTAT_HEATING',
#        0x40: 'COMMAND_CLASS_THERMOSTAT_MODE',
#        0x42: 'COMMAND_CLASS_THERMOSTAT_OPERATING_STATE',
#        0x43: 'COMMAND_CLASS_THERMOSTAT_SETPOINT',
#        0x44: 'COMMAND_CLASS_THERMOSTAT_FAN_MODE',
#        0x45: 'COMMAND_CLASS_THERMOSTAT_FAN_STATE',
#        0x46: 'COMMAND_CLASS_CLIMATE_CONTROL_SCHEDULE',
#        0x47: 'COMMAND_CLASS_THERMOSTAT_SETBACK',
#        0x4c: 'COMMAND_CLASS_DOOR_LOCK_LOGGING',
#        0x4E: 'COMMAND_CLASS_SCHEDULE_ENTRY_LOCK',
#        0x50: 'COMMAND_CLASS_BASIC_WINDOW_COVERING',
#        0x51: 'COMMAND_CLASS_MTP_WINDOW_COVERING',
#        0x60: 'COMMAND_CLASS_MULTI_CHANNEL_V2',
#        0x62: 'COMMAND_CLASS_DOOR_LOCK',
#        0x63: 'COMMAND_CLASS_USER_CODE',
#        0x70: 'COMMAND_CLASS_CONFIGURATION',
#        0x71: 'COMMAND_CLASS_ALARM',
#        0x72: 'COMMAND_CLASS_MANUFACTURER_SPECIFIC',
#        0x73: 'COMMAND_CLASS_POWERLEVEL',
#        0x75: 'COMMAND_CLASS_PROTECTION',
#        0x76: 'COMMAND_CLASS_LOCK',
#        0x77: 'COMMAND_CLASS_NODE_NAMING',
#        0x7A: 'COMMAND_CLASS_FIRMWARE_UPDATE_MD',
#        0x7B: 'COMMAND_CLASS_GROUPING_NAME',
#        0x7C: 'COMMAND_CLASS_REMOTE_ASSOCIATION_ACTIVATE',
#        0x7D: 'COMMAND_CLASS_REMOTE_ASSOCIATION',
#        0x81: 'COMMAND_CLASS_CLOCK',
#        0x82: 'COMMAND_CLASS_HAIL',
#        0x84: 'COMMAND_CLASS_WAKE_UP',
#        0x85: 'COMMAND_CLASS_ASSOCIATION',
#        0x86: 'COMMAND_CLASS_VERSION',
#        0x87: 'COMMAND_CLASS_INDICATOR',
#        0x88: 'COMMAND_CLASS_PROPRIETARY',
#        0x89: 'COMMAND_CLASS_LANGUAGE',
#        0x8A: 'COMMAND_CLASS_TIME',
#        0x8B: 'COMMAND_CLASS_TIME_PARAMETERS',
#        0x8C: 'COMMAND_CLASS_GEOGRAPHIC_LOCATION',
#        0x8D: 'COMMAND_CLASS_COMPOSITE',
#        0x8E: 'COMMAND_CLASS_MULTI_INSTANCE_ASSOCIATION',
#        0x8F: 'COMMAND_CLASS_MULTI_CMD',
#        0x90: 'COMMAND_CLASS_ENERGY_PRODUCTION',
#        0x91: 'COMMAND_CLASS_MANUFACTURER_PROPRIETARY',
#        0x92: 'COMMAND_CLASS_SCREEN_MD',
#        0x93: 'COMMAND_CLASS_SCREEN_ATTRIBUTES',
#        0x94: 'COMMAND_CLASS_SIMPLE_AV_CONTROL',
#        0x95: 'COMMAND_CLASS_AV_CONTENT_DIRECTORY_MD',
#        0x96: 'COMMAND_CLASS_AV_RENDERER_STATUS',
#        0x97: 'COMMAND_CLASS_AV_CONTENT_SEARCH_MD',
#        0x98: 'COMMAND_CLASS_SECURITY',
#        0x99: 'COMMAND_CLASS_AV_TAGGING_MD',
#        0x9A: 'COMMAND_CLASS_IP_CONFIGURATION',
#        0x9B: 'COMMAND_CLASS_ASSOCIATION_COMMAND_CONFIGURATION',
#        0x9C: 'COMMAND_CLASS_SENSOR_ALARM',
#        0x9D: 'COMMAND_CLASS_SILENCE_ALARM',
#        0x9E: 'COMMAND_CLASS_SENSOR_CONFIGURATION',
#        0xEF: 'COMMAND_CLASS_MARK',
#        0xF0: 'COMMAND_CLASS_NON_INTEROPERABLE'
#  

    def _getValuesForCommandClass(self, classId):
        """Optient la (les) valeur(s) pour une Cmd CLASS donnée  
        @ Param classid : Valeur hexa de la COMMAND_CLASS"""
        # extraction des valuesnode correspondante à classId, si pas reconnues par le node -> liste vide
        retval = list()
        classStr = PyManager.COMMAND_CLASS_DESC[classId]
        for value in self._values.itervalues():
            vdic = value.valueData
            if vdic and vdic.has_key('commandClass') and vdic['commandClass'] == classStr:
                retval.append(value)
        return retval
    
    def _updateCapabilities(self):
        """Mise à jour des capabilities set du node"""
  #      Capabilities = ['Routing', 'Listening', 'Beanning', 'Security', 'FLiRS']
        nodecaps = set()
        if self._manager.isNodeRoutingDevice(self._homeId, self._nodeId): nodecaps.add('Routing')
        if self._manager.isNodeListeningDevice(self._homeId, self._nodeId): nodecaps.add('Listening')
        if self._manager.isNodeBeamingDevice(self._homeId, self._nodeId): nodecaps.add('Beaming')
        if self._manager.isNodeSecurityDevice(self._homeId, self._nodeId): nodecaps.add('Security')
        if self._manager.isNodeFrequentListeningDevice(self._homeId, self._nodeId): nodecaps.add('FLiRS')
        self._capabilities = nodecaps
        self._ozwmanager._log.debug('Node [%d] capabilities are: %s', self._nodeId, self._capabilities)
        
    def _updateCommandClasses(self):
        """Mise à jour des command classes du node"""
        classSet = set()
        for cls in PyManager.COMMAND_CLASS_DESC:
            if self._manager.getNodeClassInformation(self._homeId, self._nodeId, cls):
                classSet.add(cls)
        self._commandClasses = classSet
        self._ozwmanager._log.debug('Node [%d] command classes are: %s', self._nodeId, self._commandClasses)
        
    def _updateInfos(self):
        """Mise à jour des informations générales du node"""
        self._name = self._manager.getNodeName(self._homeId, self._nodeId)
        self._location = self._manager.getNodeLocation(self._homeId, self._nodeId)
        self._manufacturer = NamedPair(id=self._manager.getNodeManufacturerId(self._homeId, self._nodeId), name=self._manager.getNodeManufacturerName(self._homeId, self._nodeId))
        self._product = NamedPair(id=self._manager.getNodeProductId(self._homeId, self._nodeId), name=self._manager.getNodeProductName(self._homeId, self._nodeId))
        self._productType = NamedPair(id=self._manager.getNodeProductType(self._homeId, self._nodeId), name=self._manager.getNodeType(self._homeId, self._nodeId))
        self._nodeInfos = NodeInfo(
            generic = self._manager.getNodeGeneric(self._homeId, self._nodeId),
            basic = self._manager.getNodeBasic(self._homeId, self._nodeId),
            specific = self._manager.getNodeSpecific(self._homeId, self._nodeId),
            security = self._manager.getNodeSecurity(self._homeId, self._nodeId),
            version = self._manager.getNodeVersion(self._homeId, self._nodeId)
        )
    
    def  _isSleeping(self):
        "Interroge le node pour voir son etat"
        # TODO: A perfectionner, pour l'instant uniquement basé sur la capacité du node et non son etat réel
        if 'Listening' in self._capabilities : retval = False
        else : 
            if (time.time() - self.lastUpdate) > 30 :
                retval = True
            else :  retval = False
        print '+++++ Is Sleeping ? :', retval, ' ++++'
        print "WakeUp commandClass : ",  self._manager.getNodeClassInformation(self._homeId, self._nodeId, 0x84 ) # 'COMMAND_CLASS_WAKE_UP
        return retval        
    
    def _updateNeighbors(self):
        """Mise à jour de la liste des nodes voisins"""
        # TODO: I believe this is an OZW bug, but sleeping nodes report very odd (and long) neighbor lists
        neighbors = self._manager.getNodeNeighbors(self._homeId, self._nodeId)
        if neighbors is None or neighbors == 'None':
            self._neighbors = None
        else:
            self._neighbors = neighbors
        if self.isSleeping and self._neighbors is not None and len(self._neighbors) > 10:
            self._ozwmanager._log.warning('Probable OZW bug: Node [%d] is sleeping and reports %d neighbors; marking neighbors as none.', self.id, len(self._neighbors))
            self._neighbors = None
        print ('Node [%d] neighbors are: ' %self._nodeId) , self._neighbors
        self._ozwmanager._log.debug('Node [%d] neighbors are: %s', self._nodeId, self._neighbors)

    def updateGroup(self,  groupIdx):
        """Mise à jour des informations du group/association du node """
        groups = list()
        for grp in self._groups :
            if grp.index == groupIdx : 
                mbrs = self._manager.getAssociations(self._homeId, self._nodeId, groupIdx)
                dmembers = {};
                for m in mbrs :
                    dmembers[m] = MemberGrpStatus[1]
                print("Update groupe avant :"),  grp
                grp= (GroupInfo(
                    index = groupIdx,
                    label = self._manager.getGroupLabel(self._homeId, self._nodeId, groupIdx),
                    maxAssociations = self._manager.getMaxAssociations(self._homeId, self._nodeId, groupIdx),
                    members = dmembers
                    ))
                print("Update groupe après :"),  grp
                break
            groups.append(grp)
        self._groups = groups
        print ('Node [%d] groups are: ' %self._nodeId) , self._groups
        self._ozwmanager._log.debug('Node [%d] groups are: %s', self._nodeId, self._groups)        
        
    def _updateGroups(self):
        """Mise à jour des informations de group/associationdu node """
        groups = list()
        for i in range(1, self._manager.getNumGroups(self._homeId, self._nodeId) + 1):
            mbrs = self._manager.getAssociations(self._homeId, self._nodeId, i)
            dmembers = {};
            for m in mbrs :
                dmembers[m] = MemberGrpStatus[1]
            groups.append(GroupInfo(
                index = i,
                label = self._manager.getGroupLabel(self._homeId, self._nodeId, i),
                maxAssociations = self._manager.getMaxAssociations(self._homeId, self._nodeId, i),
                members = dmembers
                ))
        self._groups = groups
        print ('Node [%d] groups are: ' %self._nodeId) , self._groups
        self._ozwmanager._log.debug('Node [%d] groups are: %s', self._nodeId, self._groups)

    def _updateConfig(self):
        self._ozwmanager._log.debug('Requesting config params for node [%d]', self._nodeId)
        self._manager.requestAllConfigParams(self._homeId, self._nodeId)

        
    def updateNode(self):
        """Mise à jour de toutes les caractéristiques du node"""
        self._updateCapabilities()
        self._updateCommandClasses()
        self._updateNeighbors()
        self._updateGroups()
        self._updateInfos()
#        self._updateConfig()
        
# Traitement spécifique
    def _getbasic(self):
        values = self._getValuesForCommandClass(0x20)   # COMMAND_CLASS_BASIC
        if values:
            for value in values:
                vdic = value.valueData
                if vdic and vdic.has_key('type') and vdic['type'] == 'Byte' and vdic.has_key('value'):
                    return int(vdic['value'])
        return 0

    def _getLevel(self):
        values = self._getValuesForCommandClass(0x26)  # COMMAND_CLASS_SWITCH_MULTILEVEL
        if values:
            for value in values:
                vdic = value.valueData
                if vdic and vdic.has_key('type') and vdic['type'] == 'Byte' and vdic.has_key('value'):
                    return int(vdic['value'])
        return 0

    def _getBatteryLevel(self):
        values = self._getValuesForCommandClass(0x80)  # COMMAND_CLASS_BATTERY
        if values:
            for value in values:
                vdic = value.valueData
                if vdic and vdic.has_key('type') and vdic['type'] == 'Byte' and vdic.has_key('value'):
                    return int(vdic['value'])
        return -1

    def _getSignalStrength(self):
        return 0

    def _getIsOn(self):
        values = self._getValuesForCommandClass(0x25)  # COMMAND_CLASS_SWITCH_BINARY
        if values:
            for value in values:
                vdic = value.valueData
                if vdic and vdic.has_key('type') and vdic['type'] == 'Bool' and vdic.has_key('value'):
                    return vdic['value'] == 'True'
        return False
 
    def getValuesForCommandClass(self, commandClass) :
        """Retourne les Values correspondant à la commandeClass"""
        classId = PyManager.COMMAND_CLASS_DESC.keys()[PyManager.COMMAND_CLASS_DESC.values().index(commandClass)]
        return self._getValuesForCommandClass(classId)

    def hasCommandClass(self, commandClass):
        """ Renvois les cmdClass demandées filtrées selon celles reconnues par le node """
        return commandClass in self._commandClasses

    def getInfos(self):
        """ Retourne les informations du device (node), format dict{} """
        retval={}
        self._updateInfos() # mise à jour selon OZW
        self._updateCommandClasses()
        retval["HomeID"] ="0x%.8x" % self.homeId
        retval["Model"]= self.manufacturer + " -- " + self.product
        retval["State sleeping"] = True if self.isSleeping else False
        retval["Node"] = self.nodeId
        retval["Name"] = self.name if self.name else 'Undefined'
        retval["Location"] = self.location if self.location else 'Undefined'
        retval["Type"] = self.productType
        retval["Last update"] = time.ctime(self.lastUpdate)
        retval["Neighbors"] = list(self.neighbors) if  self.neighbors else 'No one'
        retval["Groups"] = self._getGroupsDict()
        return retval
        
    def getValuesInfos(self):
        """ Retourne les informations de values d'un device (node), format dict{} """
        retval={}
        self._updateInfos() # mise à jour selon OZW
        retval['Values'] = []
        for value in self.values.keys():
            retval['Values'].append(self.values[value].getInfos())
        return retval
        
    def setName(self, name):
        """Change le nom du node"""
        self._manager.setNodeName(self.homeId, self.id, name)
        self._ozwmanager._log.debug('Requesting setNodeName for node {0} with new name {1}'.format(self.id, name))
 
    def setLocation(self, loc):
        """"Change la localisation du node"""
        self._manager.setNodeLocation(self.homeId, self.id, loc)   
        self._ozwmanager._log.debug('Requesting setNodeLocation for node {0} with new location {1}'.format(self.id, loc))

    def refresh(self):
        """Rafraichis le node, util dans le cas d'un reveil si le node dormait lors de l''init """
        self._manager.refreshNodeInfo(self.homeId, self.id)
        self._ozwmanager._log.debug('Requesting refresh for node {0}'.format(node.id))
        
    def addAssociation(self, groupIndex,  targetNodeId):
        """Ajout l'association du targetNode au groupe du node"""
        self._manager.addAssociation(self.homeId, self.id, groupIndex,  targetNodeId)
        self._ozwmanager._log.debug('Requesting for node {0} addAssociation node {1} in group index {2}  '.format(self.id,  targetNodeId, groupIndex))

    def removeAssociation(self, groupIndex,  targetNodeId):
        """supprime l'association du targetNode au groupe du node"""
        self._manager.removeAssociation(self.homeId, self.id, groupIndex,  targetNodeId)
        self._ozwmanager._log.debug('Requesting for node {0} removeAssociation node {1} in group index {2}  '.format(self.id,  targetNodeId, groupIndex))
        
    def setOn(self):
        """Set node on pour commandclass basic"""
        self._manager.setNodeOn(self.homeId, self.id)
        self._ozwmanager._log.debug('Requesting setNodeOn for node {0}'.format(self.id))

    def setOff(self):
        """Set node off pour commandclass basic"""
        self._manager.setNodeOff(self.homeId, self.id)
        self._ozwmanager._log.debug('Requesting setNodeOff for node {0}'.format(self.id))

    def setLevel(self, level):
        """Set node level pour commandclass basic"""
        self._manager.setNodeLevel(self.homeId, self.id, level)
        self._ozwmanager._log.debug('Requesting setNodeLevel for node {0} with new level {1}'.format(self.id, level))

    def createValue(self, valueId):
        """Crée la valueNode valueId du node si besoin et renvoie l'object valueNode."""
        vid = valueId['id']
        if self._values.has_key(vid):
            self._values[vid].updateData(valueId)
            retval = self._values[vid]
        else:
            retval = ZWaveValueNode(self, valueId)
            self._ozwmanager._log.debug('Created new value node with homeId %0.8x, nodeId %d, valueId %s', self.homeId, self.nodeId, valueId)
            self._values[vid] = retval
            print ('Created new value node with homeId %0.8x, nodeId %d, valueId %s', self.homeId, self.nodeId, valueId)
        return retval 
   
    def getValue(self, valueId):
        """Renvoi la valueNode valueId du node."""
        vid = valueId['id']
        retval= None
        if self._values.has_key(vid):
            retval = self._values[vid]
        else:
            raise OZwaveNodeException('Value get received before creation (homeId %.8x, nodeId %d, valueid %s)' % (self.homeId, self.nodeId,  valueId))
        return retval
        
    def setMembersGrps(self,  newGroups):
        """Envoie les changement des associations de nodes dans les groups d'association."""
       # groups = self._getGroupsDict()
        groups = self.groups
        print ('set members association :'), newGroups
        print ('Groups actuel : '), groups
        for gn in newGroups :
            print
            print gn
            for grp in groups :
                print grp.index
                if gn['idx'] == grp.index :
                    for mn in gn['mbs']:
                        toAdd = True
                        for m in grp.members:
                            if mn['id'] == m :
                                mn['status'] = grp.members[m]
                                toAdd = False
                                break
                        if toAdd : #TODO: vérifier que le status est bien to update
                            self.addAssociation(grp.index, mn['id'])
                            mn['status'] = MemberGrpStatus[2]
                    break
        print ('set members association add members result :'), newGroups
        for grp in groups :
            for gn in newGroups :
                if grp.index == gn['idx'] :
                    for m in grp.members:
                        toRemove = True
                        for mn in gn['mbs']:
                            if m == mn['id']:
                                print ('members not remove: '),  m
                                mn['status'] =  grp.members[m]
                                toRemove = False
                                break
                        if toRemove : #TODO: vérifier que le status est bien to update
                            print ('members remove : '),  m
                            self.removeAssociation(grp.index, m)
                            grp.members[m] = MemberGrpStatus[2]
                    break
        print ('set members association remove members result :'), newGroups 
        return newGroups
        
    def sendCmdBasic(self, instance,  command,  opt):
        """Envoie une commande au node"""
        if (opt != "") and (opt != 'None'):
            opt = int(opt)
        else : opt = 0
        if instance == 1 :
            if command == 'level':
                self.setLevel(opt)
            elif command == 'on':
                self.setOn()
            elif command == 'off':
                self.setOff()
            else : 
                self._ozwmanager._log.info("xPL to ozwave unknown command : %s , nodeId : %d",  command,  self.nodeId)
        else : # instance secondaire, utilisation de set value
            print ("instance secondaire")
            cmdsClass= ['COMMAND_CLASS_BASIC', 'COMMAND_CLASS_SWITCH_BINARY','COMMAND_CLASS_SWITCH_MULTILEVEL']
            for value in self.values.keys() :
                val = self.values[value].valueData
                print ("valeur : " + val['commandClass'])
                if (val['commandClass'] in cmdsClass)  and val['instance'] == instance :                 
                    if command=='on' : opt = 255
                    elif command=='off' : opt = 0
                    self.values[value].setValue(opt)
                    break
        print ("commande transmise")
        
    def __str__(self):
        return 'homeId: [{0}]  nodeId: [{1}] product: {2}  name: {3}'.format(self._homeId, self._nodeId, self._product, self._name)

        
