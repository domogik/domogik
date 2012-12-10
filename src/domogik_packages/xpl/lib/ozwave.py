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

from collections import namedtuple
import binascii
import threading
import libopenzwave
from libopenzwave import PyManager
from ozwvalue import ZWaveValueNode
from ozwnode import ZWaveNode
from ozwdefs import *
import time
from time import sleep
import os.path


class OZwaveManagerException(OZwaveException):
    """"Zwave Manager exception  class"""
            
    def __init__(self, value):
        OZwaveException.__init__(self, value)
        self.msg = "OZwave Manager exception:"
                                                    

class OZWavemanager(threading.Thread):
    """
    ZWave class manager
    """

    def __init__(self, config,  cb_send_xPL, cb_sendxPL_trig, stop , log,  configPath, userPath,  ozwlog = False, msgEndCb =  False):
        """ Ouverture du manager py-openzwave
            @ param config : configuration du plugin pour accès aux valeurs paramètrées"
            @ param cb_send_xpl : callback pour envoi msg xpl
            @ param cb_send_trig : callback pour trig xpl
            @ param stop : flag d'arrêt du plugin         
            @ param log : log instance domogik
            @ param configPath : chemin d'accès au répertoire de configuration pour la librairie openszwave (déf = "./../plugins/configPath/")
            @ param userPath : chemin d'accès au répertoire de sauvegarde de la config openzwave et du log."
            @ param ozwlog (optionnel) : Activation du log d'openzawe, fichier OZW_Log.txt dans le répertoire user (déf = "--logging false")
            @ param msgEndCb (désactivée pour l'instant) Envoi d'une notification quand la transaction est complete (defaut = "--NotifyTransactions  false")
        """
        self._device = None
        self._configPlug=config
        self._log = log
        self._cb_send_xPL= cb_send_xPL
        self._cb_sendxPL_trig= cb_sendxPL_trig
        self._stop = stop
        self._homeId = 0
        self._activeNodeId= None # node actif courant, pour utilisation dans les fonctions du manager
        self._ctrlnodeId = 0
        self._controller = None
        self._nodes = dict()
        self._libraryTypeName = 'Unknown'
        self._libraryVersion = 'Unknown'
        self._pyOzwlibVersion =  'Unknown'
        self._configPath = configPath
        self._userPath = userPath
        self._ready = False
        # récupération des association nom de réseaux et homeID
        self._nameAssoc ={}
        if self._configPlug != None :
            num = 1
            loop = True
            while loop == True:
                HIdName = self._configPlug.query('ozwave', 'homename-%s' % str(num))
                HIdAssoc = self._configPlug.query('ozwave', 'homeidass-%s' % str(num))
                if HIdName != None : 
                    try :
                        self._nameAssoc[HIdName] = long(HIdAssoc,  16)
                    except OZwaveManagerException as e:
                        self._log.error(e.value)
                        print e.value
                        self._nameAssoc[HIdName]  = 0
                else:
                    loop = False
                num += 1                
        print self._nameAssoc
        threading.Thread.__init__(self, target=self.run)
        autoPath = self._configPlug.query('ozwave', 'autoconfpath')
        print 'autopath : ' , autoPath
        if autoPath and libopenzwave.configPath() :
            self._configPath = libopenzwave.configPath()
        if not os.path.exists(self._configPath) : 
            self._log.debug("Directory openzwave config not exist : %s" , self._configPath)
            raise OZwaveManagerException ("Directory openzwave config not exist : %s"  % self._configPath)
            
        # Séquence d'initialisation d'openzwave
        # Spécification du chemain d'accès à la lib open-zwave
        opt=""
        if ozwlog=="True" : opts = "--logging true"
        else : opts = "--logging false"
        # if msgEndCb : opts = opts + "--NotifyTransactions true" # false par defaut  --- desactivé, comportement bizard
        self._log.info("Try to run openzwave manager")
        self.options = libopenzwave.PyOptions()
        self.options.create(self._configPath, self._userPath,  opts) 
     #   self.options.addOptionBool("NotifyTransactions", 'true')
        self.options.lock() # nécessaire pour bloquer les options et autoriser le PyManager à démarrer
        self._manager = libopenzwave.PyManager()
        self._manager.create()
        self._manager.addWatcher(self.cb_openzwave) # ajout d'un callback pour les notifications en provenance d'OZW.
        self._log.info(self.pyOZWLibVersion + " -- plugin version :" + OZWPLuginVers)
        # self.manager.addDriver(self._device)  # ajout d'un driver dans le manager, fait par self.openDevice() dans class OZwave(XplPlugin):
        print ('user config :',  self._userPath,  " Logging openzwave : ",  opts)
        print self.pyOZWLibVersion + " -- plugin version :" + OZWPLuginVers
        
     # On accède aux attributs uniquement depuis les property
    device = property(lambda self: self._device)
    homeId = property(lambda self: self._homeId)
    activeNodeId= property(lambda self: self._activeNodeId)
    controllerNode = property(lambda self: self._controller)
    controllerDescription = property(lambda self: self._getControllerDescription())
    nodes = property(lambda self: self._nodes)   
    libraryDescription = property(lambda self: self._getLibraryDescription())
    libraryTypeName = property(lambda self: self._libraryTypeName)
    libraryVersion = property(lambda self: self._libraryVersion)
    nodeCount = property(lambda self: len(self._nodes))
    nodeCountDescription = property(lambda self: self._getNodeCountDescription())
    sleepingNodeCount = property(lambda self: self._getSleepingNodeCount())
    ready = property(lambda self: self._ready)
    pyOZWLibVersion = property(lambda self: self._getPyOZWLibVersion())

    def openDevice(self, device):
        """Ajoute un controleur au manager (en developpement 1 seul controleur actuellement)"""
        # TODO: Gérer une liste de controleurs
        if self._device != None and self._device != device :
            self._log.info("Remove driver from openzwave : %s",  self._device)
            self._manager.removeDriver(self._device)
        self._device = device
        self._log.info("adding driver to openzwave : %s",  self._device)
        self._manager.addDriver(self._device)  # ajout d'un driver dans le manager
        
    def stop(self):
        """ Stop class OZWManager."""
        print("Stopping plugin, Remove driver from openzwave : %s",  self._device)
        self._log.info("Stopping plugin, Remove driver from openzwave : %s",  self._device)
        sleep(1)
        self._manager.removeDriver(self.device)
        self._ready = False

    def run(self, stop):
        """ Maintient la class OZWManager pour le fonctionnement du plugin.
        @param stop : an Event to wait for stop request."""
        # tant que le plugins est en cours mais pas lancer pour l'instant, vraiment util ?
        self._log.info("Start plugin listenner")
        print ("Start plugin listenner")
        try:
            while not stop.isSet():
                sleep (1)  # utile pour libérer le temps processeur ?
        except OZwaveManagerException :
            self._log.error("Error listener run")
            return
        print ("Stop plugin listener")
            
    def _getPyOZWLibVersion(self):
        """Renvoi les versions des librairies py-openzwave ainsi que la version d'openzwave."""
        try :
            self._pyOzwlibVersion = self._manager.getPythonLibraryVersion ()
        except :
            self._pyOzwlibVersion  =  'Unknown'
            return 'py-openzwave : < 0.1 check for update, OZW revision : Unknown'
        try :
            ozwvers = self._manager.getOzwLibraryVersion ()
        except :
            ozwvers  =  'OZW revision :Unknown < r530'            
        if self._pyOzwlibVersion :
            return '{0} , {1}'.format(self._pyOzwlibVersion,  ozwvers)
        else:
            return 'Unknown'
            
    def _getSleepingNodeCount(self):
        """ Renvoi le nombre de node en veille."""
        retval = 0
        for node in self._nodes.itervalues():
            if node.isSleeping:
                retval += 1
        return retval - 1 if retval > 0 else 0

    def _getLibraryDescription(self):
        """Renvoi le type de librairie ainsi que la version du controleur du réseaux zwave HomeID"""
        if self._libraryTypeName and self._libraryVersion:
            return '{0} Library Version {1}'.format(self._libraryTypeName, self._libraryVersion)
        else:
            return 'Unknown'

    def _getNodeCountDescription(self):
        """Renvoi le nombre de node total et/ou le nombre en veille (return str)"""
        retval = '{0} Nodes'.format(self.nodeCount)
        sleepCount = self.sleepingNodeCount
        if sleepCount:
            retval = '{0} ({1} sleeping)'.format(retval, sleepCount)
        return retval

    def _getControllerDescription(self):
        """ Renvoi la description du node actif (fabriquant et produit)"""
        if self._activeNodeId:
            node = self._getNode(self._homeId, self._activeNodeId)
            if node and node._product:
                return node._product.name
        return 'Unknown Controller'

    def cb_openzwave(self,  args):
        """Callback depuis la librairie py-openzwave 
        """
    # callback ordre : (notificationtype, homeid, nodeid, ValueID, groupidx, event) 
    # notification implémentés
#         ValueAdded = 0                    / A new node value has been added to OpenZWave's list. These notifications occur after a node has been discovered, and details of its command classes have been received.  Each command class may generate one or more values depending on the complexity of the item being represented.
#         ValueChanged = 2                  / A node value has been updated from the Z-Wave network and it is different from the previous value.
#         NodeNew = 5                       / A new node has been found (not already stored in zwcfg*.xml file)
#         NodeAdded = 6                     / A new node has been added to OpenZWave's list.  This may be due to a device being added to the Z-Wave network, or because the application is initializing itself.
#         NodeEvent = 10                    / A node has triggered an event.  This is commonly caused when a node sends a Basic_Set command to the controller.  The event value is stored in the notification.
#         DriverReady = 18                  / A driver for a PC Z-Wave controller has been added and is ready to use.  The notification will contain the controller's Home ID, which is needed to call most of the Manager methods.
#         NodeQueriesComplete = 23          / All the initialisation queries on a node have been completed.
#         AwakeNodesQueried = 24            / All awake nodes have been queried, so client application can expected complete data for these nodes.
#         AllNodesQueried = 25              / All nodes have been queried, so client application can expected complete data.

#TODO: notification à implémenter
#         ValueRemoved = 1                  / A node value has been removed from OpenZWave's list.  This only occurs when a node is removed.
#         ValueRefreshed = 3                / A node value has been updated from the Z-Wave network.
#         Group = 4                         / The associations for the node have changed. The application should rebuild any group information it holds about the node.
#         NodeRemoved = 7                   / A node has been removed from OpenZWave's list.  This may be due to a device being removed from the Z-Wave network, or because the application is closing.
#         NodeProtocolInfo = 8              / Basic node information has been receievd, such as whether the node is a listening device, a routing device and its baud rate and basic, generic and specific types. It is after this notification that you can call Manager::GetNodeType to obtain a label containing the device description.
#         NodeNaming = 9                    / One of the node names has changed (name, manufacturer, product).
#         PollingDisabled = 11              / Polling of a node has been successfully turned off by a call to Manager::DisablePoll
#         PollingEnabled = 12               / Polling of a node has been successfully turned on by a call to Manager::EnablePoll
#         SceneEvent = 13                 / Scene Activation Set received
#         CreateButton = 14                 / Handheld controller button event created 
#         DeleteButton = 15                 / Handheld controller button event deleted 
#         ButtonOn = 16                     / Handheld controller button on pressed event
#         ButtonOff = 17                    / Handheld controller button off pressed event 
#         DriverFailed = 19                 / Driver failed to load
#         DriverReset = 20                  / All nodes and values for this driver have been removed.  This is sent instead of potentially hundreds of individual node and value notifications.
#         MsgComplete = 21                  / The last message that was sent is now complete.
#         EssentialNodeQueriesComplete = 22 / The queries on a node that are essential to its operation have been completed. The node can now handle incoming messages.
#         Error = 26                        / An error has occured that we need to report.

        print('\n%s\n[%s]:' % ('-'*20, args['notificationType']))
        print args
        notifyType = args['notificationType']
        if notifyType == 'DriverReady':
            self._handleDriverReady(args)
  #      if notifyType == 'NodeProtocolInfo':
  #          self._handleDriverReady(args)           
        elif notifyType in ('NodeAdded', 'NodeNew'):
            self._handleNodeChanged(args)
        elif notifyType == 'ValueAdded':
            self._handleValueAdded(args)
        elif notifyType == 'ValueChanged':
            self._handleValueChanged(args)
        elif notifyType == 'NodeEvent':
            self._handleNodeEvent(args)
        elif notifyType == 'Group':
            self._handleGroupChanged(args)
        elif notifyType == 'NodeQueriesComplete':
            self._handleNodeQueryComplete(args)
        elif notifyType in ('AwakeNodesQueried', 'AllNodesQueried'):
            self._handleInitializationComplete(args)

        else : 
            self._log.info("zwave callback : %s is not handled yet",  notifyType)
            self._log.info(args)
    
    def _handleDriverReady(self, args):
        """Appelé une fois que le controleur est déclaré et initialisé dans OZW.
        l'HomeID et NodeID du controlleur sont enregistrés."""
        self._homeId = args['homeId']
        self._activeNodeId= args['nodeId']
        self._libraryVersion = self._manager.getLibraryVersion(self._homeId)
        self._libraryTypeName = self._manager.getLibraryTypeName(self._homeId)
        self._ctrlnodeId =  self._activeNodeId
        self._log.info("Device %s ready. homeId is 0x%0.8x, controller node id is %d, using %s library version %s", self._device,  self._homeId, self._activeNodeId, self._libraryTypeName, self._libraryVersion)
        self._log.info('OpenZWave Initialization Begins.')
        self._log.info('The initialization process could take several minutes.  Please be patient.')
        print ('controleur prêt' )
        
    def _handleNodeQueryComplete(self, args):
        """Les requettes d'initialisation du node sont complété."""
        node = self._getNode(self._homeId, args['nodeId'])
        node.updateNode()
        self._controller = self._getNode(self._homeId, self._ctrlnodeId )
        self._log.info('Z-Wave Device Node {0} is ready.'.format(node.id))

    def _getNode(self, homeId, nodeId):
        """ Renvoi l'objet node correspondant"""
        return self._nodes[nodeId] if self._nodes.has_key(nodeId) else None
        
    def _fetchNode(self, homeId, nodeId):
        """ Renvoi et construit un nouveau node s'il n'existe pas et l'enregistre dans le dict """
        retval = self._getNode(homeId, nodeId)
        if retval is None:
            retval = ZWaveNode(self,  homeId, nodeId)
            self._log.debug('Created new node with homeId 0x%0.8x, nodeId %d', homeId, nodeId)
            self._nodes[nodeId] = retval
        return retval

    def _handleNodeChanged(self, args):
        """Un node est ajouté ou nouveau"""
        node = self._fetchNode(args['homeId'], args['nodeId'])
        node._lastUpdate = time.time()
        self._log.info ('Node %d as add (homeId %.8x)' , args['nodeId'],  args['homeId'])

    def _handleValueAdded(self, args):
        """Un valueNode est ajouté au node depuis le réseaux zwave"""
        homeId = args['homeId']
        activeNodeId= args['nodeId']
        valueId = args['valueId']
        node = self._fetchNode(homeId, activeNodeId)
        node._lastUpdate = time.time()
        node.createValue(valueId)
       
    def _handleValueChanged(self, args):
        """"Un valuenode à changé sur le réseaux zwave"""
        sendxPL = False
        homeId = args['homeId']
        activeNodeId= args['nodeId']
        valueId = args['valueId']
        node = self._fetchNode(homeId, activeNodeId)
   #     node._sleeping = False # TODO: pas sur que le device soit réèlement sortie du mode spleeping
        node._lastUpdate = time.time()
        valueNode = node.getValue(valueId)
        valueNode.updateData(valueId) 
        print node.commandClasses 
        # formattage infos générales
        msgtrig = {'typexpl':'xpl-trig',
                          'addressety' : "%s.%d.%d" %(self._nameAssoc.keys()[self._nameAssoc.values().index(homeId)] , activeNodeId,valueId['instance']) ,               
                          'valuetype':  valueId['type'], 
                          'type' : valueId['label'].lower()}  # ici l'idée est de passer tout les valeurs stats et trig en identifiants leur type par le label forcé en minuscule.
                                                                            # les labels sont listés dans les tableaux des devices de la page spéciale, il faut les saisir dans sensor.basic-ozwave.xml.
#        Le traitement pour chaque command_class s'effectue danqs la ValueNode correspondante.
        msgtrig= valueNode.valueToxPLTrig(msgtrig)
        if msgtrig: self._cb_sendxPL_trig(msgtrig)
        else : print ('commande non  implémentée vers xPL : %s'  % valueId['commandClass'] )

    def _handleNodeEvent(self, args):
        """Un node à envoyé une Basic_Set command  au controlleur.  
        Cette notification est générée par certains capteur,  comme les decteurs de mouvement type PIR, pour indiquer qu'un événements a été détecter.
        Elle est aussi envoyée dans le cas d'une commande locale d'un device. """
        CmdsClassBasicType = ['COMMAND_CLASS_SWITCH_BINARY', 'COMMAND_CLASS_SENSOR_BINARY', 'COMMAND_CLASS_SENSOR_MULTILEVEL', 
                                             'COMMAND_CLASS_SWITCH_MULTILEVEL',  'COMMAND_CLASS_SWITCH_ALL',  'COMMAND_CLASS_SWITCH_TOGGLE_BINARY',  
                                            'COMMAND_CLASS_SWITCH_TOGGLE_MULTILEVEL', 'COMMAND_CLASS_SENSOR_MULTILEVEL', ]
        sendxPL = False
        homeId = args['homeId']
        activeNodeId= args['nodeId']
        # recherche de la valueId qui a envoyée le NodeEvent
        node = self._fetchNode(homeId, activeNodeId)
        values = node.getValuesForCommandClass('COMMAND_CLASS_BASIC')
        print "*************** Node event handle *******"
        print node.productType
        if len(node.commandClasses) == 0 : node._updateCommandClasses()
        print node.commandClasses 
        args2 = ""
        for classId in node.commandClasses :
            if PyManager.COMMAND_CLASS_DESC[classId] in CmdsClassBasicType :
                valuebasic = node.getValuesForCommandClass(PyManager.COMMAND_CLASS_DESC[classId] )
                args2 = dict(args)
                del args2['event']
                valuebasic[0].valueData['value'] = args['event']
                args2['valueId'] = valuebasic[0].valueData
                args2['notificationType'] = 'ValueChanged'
                break
        print "Valeur event :" ,  args['event']
        for value in values :
            print "-- Value :"
            print value
        if args2 :
                print "Event transmit à ValueChanged :"
                print args2
                self._handleValueChanged(args2)
                print"********** Node event handle fin du traitement ******"        
                
    def _handleInitializationComplete(self, args):
        # La séquence d'initialisation est terminée
        controllercaps = set()
        if self._manager.isPrimaryController(self._homeId): controllercaps.add('primaryController')
        if self._manager.isStaticUpdateController(self._homeId): controllercaps.add('staticUpdateController')
        if self._manager.isBridgeController(self._homeId): controllercaps.add('bridgeController')
        self._controllerCaps = controllercaps
        self._log.info('Controller capabilities are: %s', controllercaps)
        for node in self._nodes.values():  
            node.updateNode() # Pourrait être utile si un node s'est réveillé pendant l'init
            node._updateConfig()
        self._ready = True
        print ("OpenZWave initialization is complete.  Found {0} Z-Wave Device Nodes ({1} sleeping)".format(self.nodeCount, self.sleepingNodeCount))
        self._log.info("OpenZWave initialization is complete.  Found {0} Z-Wave Device Nodes ({1} sleeping)".format(self.nodeCount, self.sleepingNodeCount))
        #self._manager.writeConfig(self._homeId)

    def _handleGroupChanged(self, args):
        """Report de changement d'association au seins d'un groupe"""
        node = self._fetchNode(args['homeId'], args['nodeId'])
        node.updateGroup(args['groupIdx'])
         
    def getCommandClassName(self, commandClassCode):
        return PyManager.COMMAND_CLASS_DESC[commandClassCode]

    def getCommandClassCode(self, commandClassName):
        for k, v in PyManager.COMMAND_CLASS_DESC.iteritems():
            if v == commandClassName:
                return k
        return None
        
    def _getValue(self, valueId):
        """Return l'objet Value correspondant au valueId"""
        retval= None
        for node in self._nodes.values():
            if node._values.has_key(valueId):
                retval = node._values[valueId]
                break
        return retval
       
    def getNetworkInfo(self):
        """ Retourne les infos principales du réseau zwave (dict) """
        retval={}
        retval["ConfigPath"] = self._configPath
        retval["UserPath"] = self._userPath
        retval["PYOZWLibVers"] = self.pyOZWLibVersion
        retval["OZWPluginVers"] = OZWPLuginVers
        if self.ready :
            retval["HomeID"] ="0x%.8x" % self.homeId
            retval["Model"]= self.controllerNode.manufacturer + " -- " + self.controllerNode.product
            retval["Primary controller"] = self.controllerDescription
            retval["Device"] = self.device
            retval["Node"] = self.controllerNode.nodeId
            retval["Library"] = self._libraryTypeName
            retval["Version"] = self._libraryVersion
            retval["Node count"] = self.nodeCount
            retval["Node sleeping"] = self.sleepingNodeCount
            retval["error"] =""
            ln = []
            for n in self.nodes : ln.append(n)
            retval["ListNodeId"] = ln
            print'**** getNetworkinfo : ',  retval
            return retval
        else : 
            retval["error"] = "Zwave network not ready, be patient..."
            return retval
        
    def saveNetworkConfig(self):
        """Enregistre le configuration au format xml"""
        retval = {}
        self._manager.writeConfig(self.homeId)
        print "config sauvée"
        retval["File"] ="confirmed"
        return retval

    def getZWRefFromxPL(self, addresseTy):
        """ Retourne  les références Zwave envoyées depuis le xPL domogik 
        @ param : addresseTy format : nomReseaux.NodeID.Instance """
        ids = addresseTy.split('.')
        retval ={}
        retval['homeId'] = self._nameAssoc[ids[0]] if self._nameAssoc[ids[0]]  else self.homeId
        if (retval['homeId'] == 0) : retval['homeId'] = self.homeId # force le homeid si pas configuré correctement, TODO: gérer un message pour l'utilisateur pour erreur de config.
        retval['nodeId']  = int(ids[1])
        retval['instance']  = int(ids[2])
        print "getZWRefFromxPL : ", retval
        return retval
        
    def sendNetworkZW(self, command,  addresseTy, opt =""):
        """ En provenance du réseaux xPL
              Envoie la commande sur le réseaux zwave  """ 
        print ("envoi zwave command %s" % command)
        if addresseTy != None :
            addrZW = self.getZWRefFromxPL(addresseTy)
            nodeID = int(addrZW['nodeId'])
            homeId = addrZW['homeId'] # self.homeId
            instance = addrZW['instance']
            node = self._getNode(homeId,  nodeID)
            node.sendCmdBasic(instance, command, opt)

    def getNodeInfos(self,  nodeID):
        """ Retourne les informations d'un device, format dict{} """
        if self.ready :
            node = self._getNode(self.homeId,  nodeID)
            return node.getInfos()
        else : return {"error" : "Zwave network not ready, can't find node %d" % nodeID}
        
    def getNodeValuesInfos(self,  nodeID):
        """ Retourne les informations de values d'un device, format dict{} """
        retval={}
        if self.ready :
            node = self._getNode(self.homeId,  nodeID)
            return node.getValuesInfos()
        else : return {"error" : "Zwave network not ready, can't find node %d" %nodeID}
        
    def getValueInfos(self,  valId):
        """ Retourne les informations d'une value d'un device, format dict{} """
        retval={}
        if self.ready :
            value = self._getValue(valId)
            if value :
                retval = value.getInfos()
                retval['error'] = ""
                return retval
            else : return {"error" : "Unknown value %d" %valId}
        else : return {"error" : "Zwave network not ready, can't find value %d" %valId}
        
    def getValueTypes(self):
        """Retourne la liste des type de value possible et la doc"""
        retval ={}
        for elem in  libopenzwave.PyValueTypes :
            retval[elem] = elem.doc
        return retval
           
    def setUINodeNameLoc(self,  nodeID,  newname, newloc):
        """Change le nom et/ou le localisation du node dans OZW et dans le decive si celui-ci le supporte """
        if self.ready :
            node = self._getNode(self.homeId,  nodeID)
            if node.name != newname :
                node.setName(newname)
            if node.location != newloc :
                node.setLocation(newloc)
            return node.getInfos()                                
        else : return {"error" : "Zwave network not ready, can't find node %d" %nodeID}
        
    def setValue(self,  valueId,  newValue):
        """Envoie la valeur a l'objet value"""
        retval={}
        if self.ready :
            value = self._getValue(valueId)
            if value :
                retval['value'] = value.setValue(newValue)
          #      print ('SetValue, relecture de la valeur : ',  value.getOZWValue())
                retval['error'] = ""
                return retval
            else : return {"error" : "Unknown value %d" %valId}
        else : return {"error" : "Zwave network not ready, can't find value %d" %valId}     

    def setMembersGrps(self,  nodeID,  newGroups):
        """Envoie les changement des associations de nodes dans les groups d'association."""
        retval={}
        if self.ready :
            node = self._getNode(self.homeId,  nodeID)
            grp =node.setMembersGrps(newGroups);
            if grp :
                retval['groups'] = grp
                retval['error'] = ""
                return retval
            else : return {"error" : "Manager not send association changement on node %d." %nodeID}
            return 
        else : return {"error" : "Zwave network not ready, can't find node %d" % nodeID}
                
