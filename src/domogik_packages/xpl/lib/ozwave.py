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
import urllib2
import urllib
from domogik.common.configloader import Loader

from collections import namedtuple
import binascii
import threading
import libopenzwave
from libopenzwave import PyManager
from ozwvalue import ZWaveValueNode
from ozwnode import ZWaveNode
from ozwctrl import ZWaveController
from ozwxmlfiles import *
from ozwmonitornodes import ManageMonitorNodes
from wsuiserver import BroadcastServer 
from ozwdefs import *
from datetime import timedelta,  datetime
import pwd
import sys
import resource
import traceback
import tailer

# import time
# from time import sleep
# import os.path


class OZwaveManagerException(OZwaveException):
    """"Zwave Manager exception  class"""
            
    def __init__(self, value):
        OZwaveException.__init__(self, value)
        self.msg = "OZwave Manager exception:"
                                                    

class OZWavemanager(threading.Thread):
    """
    ZWave class manager
    """

    def __init__(self, main,  config,  cb_send_xPL, cb_sendxPL_trig, stop , log,  configPath, userPath, ozwlog = False):
        """ Ouverture du manager py-openzwave
            @ param config : configuration du plugin pour accès aux valeurs paramètrées"
            @ param cb_send_xpl : callback pour envoi msg xpl
            @ param cb_send_trig : callback pour trig xpl
            @ param stop : flag d'arrêt du plugin         
            @ param log : log instance domogik
            @ param configPath : chemin d'accès au répertoire de configuration pour la librairie openszwave (déf = "./../plugins/configPath/")
            @ param userPath : chemin d'accès au répertoire de sauvegarde de la config openzwave et du log."
            @ param ozwlog (optionnel) : Activation du log d'openzawe, fichier OZW_Log.txt dans le répertoire user (déf = "--logging false")
        """
        self._main = main
        self._device = None
        self.monitorNodes = None
        self._configPlug = config
        self._log = log
        self._cb_send_xPL = cb_send_xPL
        self._cb_sendxPL_trig = cb_sendxPL_trig
        self._stop = stop
        
        # Get config rest domogik
        self.conf_rest = {'rest_ssl_certificate': '', 'rest_server_ip': '127.0.0.1', 'rest_server_port': '40405', 'rest_use_ssl': 'False'}
        cfg_rest = Loader('rest')
        config_rest = cfg_rest.load()
        self.conf_rest = dict(config_rest[1])
        
        self._homeId = 0
        self._activeNodeId = None # node actif courant, pour utilisation dans les fonctions du manager
        self._ctrlnodeId = None
        self._controller = None
        self._timeStarted = 0
        self._nodes = dict()
        self._libraryTypeName = 'Unknown'
        self._libraryVersion = 'Unknown'
        self._pyOzwlibVersion =  'Unknown'
        self._configPath = configPath
        self._userPath = userPath
        self._ready = False
        self._initFully = False
        self._ctrlActProgress = None
        self.lastTest = 0
        self.serverUI = None
        self._completMsg = self._configPlug.query('ozwave', 'cpltmsg')
        self._wsPort = int(self._configPlug.query('ozwave', 'wsportserver'))
        self._device = self._configPlug.query('ozwave', 'device')
        # récupération des associations nom de réseaux et homeID
        self._nameAssoc = {}
        if self._configPlug != None :
            num = 1
            loop = True
            while loop == True:
                HIdName = self._configPlug.query('ozwave', 'homename-%s' % str(num))
                HIdAssoc = self._configPlug.query('ozwave', 'homeidass-%s' % str(num))
                if HIdName != None : 
                    try :
                        self._nameAssoc[HIdName] = long(HIdAssoc,  16)
                    except Exception as e:
                        self._log.error("Convertion HIdAssoc parameter error : " + e.message  + ". Forced to '0'")
                        print "Convertion HIdAssoc parameter error : " + e.message + ". Forced to '0'"
                        self._nameAssoc[HIdName]  = 0
                else:
                    loop = False
                num += 1                
        print self._nameAssoc
        autoPath = self._configPlug.query('ozwave', 'autoconfpath')
        user = pwd.getpwuid(os.getuid())[0]
        if autoPath and libopenzwave.configPath() :
            self._configPath = libopenzwave.configPath()
        if not os.path.exists(self._configPath) : 
            self._log.error("Directory openzwave config not exist : %s" , self._configPath)
            raise OZwaveManagerException ("Directory openzwave config not exist : %s"  % self._configPath)
        elif not os.access(self._configPath,  os.R_OK) :
            self._log.error("User %s haven't write access on openzwave directory : %s"  %(user,  self._configPath))
            raise OZwaveManagerException ("User %s haven't write access on openzwave directory : %s"  %(user,  self._configPath))
        print "User : %s, openzwave path : %s"  % (user,  self._configPath)
        if not os.path.exists(self._userPath) : 
            self._log.info("Directory openzwave user not exist, trying create : %s" , self._configPath)
            try : 
                os.mkdir(self._userPath)
                print ("User openzwave directory created : %s"  %self._userPath)
            except Exception as e:
                self._log.error(e.message)
                print e.message
                raise OZwaveManagerException ("Directory openzwave config not exist : %s"  % self._configPath)
        if not os.access(self._userPath,  os.W_OK) :
            self._log.error("User %s haven't write access on user openzwave directory : %s"  %(user,  self._configPath))
            raise OZwaveManagerException ("User %s haven't write access on user openzwave directory : %s"  %(user,  self._configPath))
        # Séquence d'initialisation d'openzwave
        # Spécification du chemain d'accès à la lib open-zwave
        opt = ""
        if ozwlog == "True" : 
            self._ozwLog = True
            opts = "--logging true"
        else : 
            self._ozwLog = False
            opts = "--logging false"
        self._log.info("Try to run openzwave manager")
        self.options = libopenzwave.PyOptions()
        self.options.create(self._configPath, self._userPath,  opts)
        if self._completMsg: self.options.addOptionBool('NotifyTransactions',  self._completMsg)
        self.options.lock() # nécessaire pour bloquer les options et autoriser le PyManager à démarrer
        self._manager = libopenzwave.PyManager()
        self._manager.create()
        self._manager.addWatcher(self.cb_openzwave) # ajout d'un callback pour les notifications en provenance d'OZW.
        self._log.info(self.pyOZWLibVersion + " -- plugin version :" + OZWPLuginVers)
        self._log.info('Config path : ' + self._configPath)
        self._log.info('User path : ' + self._userPath)
        self._log.info('Openzwave options : {0}, NotifyTransactions : {1}'.format(opts, self._completMsg))
        print 'User config : {0}; Openzwave options : {1}, NotifyTransactions : {2}'.format(self._userPath, opts, self._completMsg)
        print self.pyOZWLibVersion + " -- plugin version :" + OZWPLuginVers
        self.getManufacturers()
        self.starter = threading.Thread(None, self.startServices, "th_Start_Ozwave_Services", (), {} )
                
     # On accède aux attributs uniquement depuis les property
    device = property(lambda self: self._device)
    homeId = property(lambda self: self._homeId)
    activeNodeId = property(lambda self: self._activeNodeId)
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

    def startServices(self):
        """démarre les differents services (wsServer, monitorNodes, le controleurZwave.
            A appeler dans un thread à la fin de l'init du pluginmanager."""
        self._log.info("Start Ozwave services in 100ms...")
        self._stop.wait(0.1) # s'assurer que l'init du pluginmanager est achevé
        self.serverUI =  BroadcastServer(self._wsPort,  self.cb_ServerWS,  self._log) # demarre le websocket server
        self._cb_send_xPL({'type':'xpl-trig', 'schema':'ozwctrl.basic',
                                      'data': {'device': self._getCtrlDeviceName(),
                                            'status':'started plugin',
                                            'type': 'status',
                                            'node': 'controller', 
                                            'usermsg': 'Plugin is in intialization process, be patient...',
                                            'data': {'state':'wsserver_started', 'wsport': self._wsPort}}})
        self.monitorNodes = ManageMonitorNodes(self)
        self.monitorNodes.start()  # demarrer la surveillance des nodes pour helper log
        # Ouverture du controleur principal
        self.openDevice(self._device)
                
    def openDevice(self, device):
        """Ajoute un controleur au manager (en developpement 1 seul controleur actuellement)"""
        # TODO: Gérer une liste de controleurs
        if self._device != None and self._device != device and self.ready :
            self._log.info("Remove driver from openzwave : %s",  self._device)
            self._manager.removeDriver(self._device)
        self._device = device
        self._log.info("Adding driver to openzwave : %s",  self._device)
        self._cb_send_xPL({'type':'xpl-trig', 'schema':'ozwctrl.basic',
                    'data': {'type': 'status', 'device': self._getCtrlDeviceName(), 'status':'started'}})
        self._manager.addDriver(self._device)  # ajout d'un driver dans le manager
        
    def closeDevice(self, device):
        """ferme un controleur du manager (en developpement 1 seul controleur actuellement)"""
        if self._device == device and self._ctrlnodeId :
            print("Remove driver from openzwave : %s" %self._device)
            self._log.info("Remove driver from openzwave : %s",  self._device)
            self._manager.removeDriver(self._device)
            self._ready = False
            self._ctrlnodeId = None
            self.serverUI.broadcastMessage({'node': 'controller', 'type': 'driver-remove', 'usermsg' : 'Driver removed.', 'data': False})
            self._cb_send_xPL({'type':'xpl-trig', 'schema':'ozwctrl.basic',
                            'data': {'type': 'status', 'device': self._getCtrlDeviceName(), 'status':'no-Ctrl'}})
            self._controller = None
        else:
            print('No controller to close')
            
    def stop(self):
        """ Stop class OZWManager."""
        print("Stopping plugin, Remove driver from openzwave : %s" %self._device)
        self._log.info("Stopping plugin, Remove driver from openzwave : %s",  self._device)
        self.closeDevice(self._device)
        self._device = None
        if self.serverUI : 
            self.serverUI.broadcastMessage({'node': 'controller', 'type': 'driver-remove', 'usermsg' : 'Plugin stopped.', 'data': False})
            self.serverUI.close()
        if self._main. _ctrlHBeat: self._main. _ctrlHBeat.stop()
    
    def _getXplCtrlState(self):
        """Envoi un hbeat de l'atat du controlleur zwave sur le hub xPl"""
        if self.ready :
            if self._ctrlActProgress and self._ctrlActProgress.has_key('state') and self._ctrlActProgress['state'] == self._controller.SIGNAL_CTRL_WAITING : st ='Lock'
            elif self._initFully : st= 'ok'
            else : st = 'init...'
        elif self._ctrlnodeId : st = 'started'
        else : st = 'no-Ctrl'
        self._cb_send_xPL({'type':'xpl-trig', 'schema':'ozwctrl.basic',
                                   'data': {'type': 'status', 'device': self._getCtrlDeviceName(), 'status':st}})
        
    def GetPluginInfo(self):
        """Renvoi les information d'état et de connection du plugin."""
        retval = {"hostport": self._wsPort,  "ctrlready": self._ready}
        if self._initFully :
            retval["Init state"] = NodeStatusNW[2] # Completed
        else :
            retval["Init state"] = NodeStatusNW[3] # In progress - Devices initializing
        retval["error"] = ""
        return retval
    
    def getManufacturers(self):
        """"Renvoi la list (dict) de tous le fabriquants et produits reconnus par la lib openzwave."""
        self.manufacturers = Manufacturers(self._configPath)
        
    def getAllProducts(self):
        """"Renvoi la list (dict) de tous le fabriquants et produits reconnus par la lib openzwave."""
        if self.manufacturers :
            return self.manufacturers.getAllProductsName()
        else :
            return {error: 'Manufacturers xml file not loaded.'}
        
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
            
    def getLoglines(self, message):
        """Renvoi les lignes Start à End du fichier de log."""
        retval = {'error': ""}
        try :
            if 'lines' in message:
                lines = int(message['lines'])
        except :
            lines = 50
        try:
           # filename = os.path.join("/var/log/domogik/ozwave.log")
            for h in self._log.__dict__['handlers']:
                if h.__class__.__name__ in ['FileHandler', 'TimedRotatingFileHandler','RotatingFileHandler', 'WatchedFileHandler']:
                    filename = h.baseFilename
            
            if message['from'] == 'top':
                retval['data'] = tailer.head(open(filename), lines)
            elif message['from'] == 'end':
                retval['data'] = tailer.tail(open(filename), lines)
            else: return {'error': "No from direction define."}
        except:
                retval['error'] = "Exception : %s" % (traceback.format_exc())
                self._log.error("Get log lines : " + retval['error'])
        return retval
        
    def getLogOZWlines(self, message):
        """Renvoi les lignes Start à End du fichier de log d'openzwave (OZW_Log.txt)."""
        if not self._ozwLog : return {'error': "Openzwave log disable, enabled it with plugin parameter and restart plugin."}
        filename = os.path.join(self._userPath + "OZW_Log.txt")        
        if not os.path.isfile(filename) : return {'error': "No existing openzwave log file : " + filename}
        retval = {'error': ""}
        try :
            if 'lines' in message:
                lines = int(message['lines'])
        except :
            lines = 50
        try:
            if message['from'] == 'top':
                retval['data'] = tailer.head(open(filename), lines)
            elif message['from'] == 'end':
                retval['data'] = tailer.tail(open(filename), lines)
            else: return {'error': "No from direction define."}
        except :
                retval['error'] = "Exception : %s" % (traceback.format_exc())
                self._log.error("Get log openzwave lines : " + retval['error'])
        return retval

    def _getSleepingNodeCount(self):
        """ Renvoi le nombre de node en veille."""
        retval = 0
        for node in self._nodes.itervalues():
            if node.isSleeping:
                retval += 1
        return retval - 1 if retval > 0 else 0

    def getMemoryUsage(self):
        """Renvoi l'utilisation memoire du plugin"""
        total = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        tplugin = sys.getsizeof(self) + sum(sys.getsizeof(v) for v in self.__dict__.values()) + self._main.getsize()
        if self.manufacturers : tplugin += self.manufacturers.getMemoryUsage();
        for n in self._nodes :
            tplugin += self._nodes[n].getMemoryUsage()
        tplugin= tplugin/1024
        retval = {'Plugin manager with ' + str(len(self._nodes)) + ' nodes' : '%s kbytes' %  tplugin}        
        retval ['Total memory use'] = '%s Mo' % (total / 1024.0)
        retval ['Openzwave'] = '%s ko' % (total - tplugin)
        return retval
    
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
        
    def _getCtrlDeviceName(self):
        if self._controller :
            self._log.debug("_getCtrlDeviceName return self._controller : {0}".format(self._controller.ctrlDeviceName))
            return self._controller.ctrlDeviceName
        else : 
            if self.conf_rest['rest_use_ssl'] == 'False' : protocol = 'http'
            else : protocol = 'https'
            rest = "%s://%s:%s" % (protocol, self.conf_rest['rest_server_ip'], self.conf_rest['rest_server_port'])
            the_url = "%s/base/device/list" % (rest)
            try :
                req = urllib2.Request(the_url)
                handle = urllib2.urlopen(req)
                devices = handle.read()
            except IOError,  e:
                self._log.warning("_getCtrlDeviceName rest error url :{0}, result :{1}".format(the_url,  e.reason))
                raise OZwaveManagerException ("rest url :{0}, {1}".format(the_url,  e.reason))
                return "UnresearchableCtrl.1.1"
            else :    
                ret = json.loads(devices)
                if ret["status"] == "OK" :
                    for dev in ret["device"]:
                        if  dev['device_type_id'] == 'ozwave.ctrl' : 
                            self._log.debug("_getCtrlDeviceName return dev['address']: {0}".format(dev['address']))
                            return dev['address']
                else :
                    n = str(self._nameAssoc.keys() [0])
                    if n : 
                        self._log.debug("_getCtrlDeviceName return self._nameAssoc.keys() [0]): {0}.1.1".format(n))
                        return "%s.1.1" % (n)
                    else :
                        self._log.warning("_getCtrlDeviceName return default: CtrlMustBeCreate.1.1")
                        return "CtrlMustBeCreate.1.1"

    def cb_openzwave(self,  args):
        """Callback depuis la librairie py-openzwave 
        """
    # callback ordre : (notificationtype, homeId, nodeId, ValueID, groupidx, event) 
    # notification implémentés
#         ValueAdded = 0                    / A new node value has been added to OpenZWave's list. These notifications occur after a node has been discovered, and details of its command classes have been received.  Each command class may generate one or more values depending on the complexity of the item being represented.
#         ValueRemoved = 1                  / A node value has been removed from OpenZWave's list.  This only occurs when a node is removed.
#         ValueChanged = 2                  / A node value has been updated from the Z-Wave network and it is different from the previous value.
#         Group = 4                         / The associations for the node have changed. The application should rebuild any group information it holds about the node.
#         NodeNew = 5                       / A new node has been found (not already stored in zwcfg*.xml file)
#         NodeAdded = 6                     / A new node has been added to OpenZWave's list.  This may be due to a device being added to the Z-Wave network, or because the application is initializing itself.
#         NodeRemoved = 7                   / A node has been removed from OpenZWave's list.  This may be due to a device being removed from the Z-Wave network, or because the application is closing.
#         NodeProtocolInfo = 8              / Basic node information has been receievd, such as whether the node is a listening device, a routing device and its baud rate and basic, generic and specific types. It is after this notification that you can call Manager::GetNodeType to obtain a label containing the device description.
#         NodeNaming = 9                    / One of the node names has changed (name, manufacturer, product).
#         NodeEvent = 10                    / A node has triggered an event.  This is commonly caused when a node sends a Basic_Set command to the controller.  The event value is stored in the notification.
#         PollingDisabled = 11              / Polling of a node has been successfully turned off by a call to Manager::DisablePoll
#         PollingEnabled = 12               / Polling of a node has been successfully turned on by a call to Manager::EnablePoll
#         DriverReady = 18                  / A driver for a PC Z-Wave controller has been added and is ready to use.  The notification will contain the controller's Home ID, which is needed to call most of the Manager methods.
#         EssentialNodeQueriesComplete = 21 / The queries on a node that are essential to its operation have been completed. The node can now handle incoming messages.
#         NodeQueriesComplete = 22          / All the initialisation queries on a node have been completed.
#         AwakeNodesQueried = 23            / All awake nodes have been queried, so client application can expected complete data for these nodes.
#         AllNodesQueried = 24              / All nodes have been queried, so client application can expected complete data.
#         AllNodesQueriedSomeDead = 25      / All nodes have been queried but some dead nodes found.
#         Notification = 26                        / An error has occured that we need to report.

#TODO: notification à implémenter
#         ValueRefreshed = 3                / A node value has been updated from the Z-Wave network.
#         SceneEvent = 13                 / Scene Activation Set received
#         CreateButton = 14                 / Handheld controller button event created 
#         DeleteButton = 15                 / Handheld controller button event deleted 
#         ButtonOn = 16                     / Handheld controller button on pressed event
#         ButtonOff = 17                    / Handheld controller button off pressed event 
#         DriverFailed = 19                 / Driver failed to load
#         DriverReset = 20                  / All nodes and values for this driver have been removed.  This is sent instead of potentially hundreds of individual node and value notifications.

        self.monitorNodes.openzwave_report(args)
        print('\n%s\n[%s]:' % ('-'*20, args['notificationType']))
        print args
        notifyType = args['notificationType']
        if notifyType == 'DriverReady':
            self._handleDriverReady(args)          
        elif notifyType in ('NodeAdded', 'NodeNew'):
            self._handleNodeChanged(args)
        elif notifyType == 'NodeRemoved':
            self._handleNodeRemoved(args)
        elif notifyType == 'ValueAdded':
            self._handleValueAdded(args)
        elif notifyType == 'ValueRemoved':
            self._handleValueRemoved(args)
        elif notifyType == 'ValueChanged':
            self._handleValueChanged(args)
        elif notifyType == 'NodeEvent':
            self._handleNodeEvent(args)
        elif notifyType == 'Group':
            self._handleGroupChanged(args)
        elif notifyType in ('AwakeNodesQueried', 'AllNodesQueried'):
            self._handleInitializationComplete(args)
        elif notifyType in ('AllNodesQueriedSomeDead'):
            self._handleMarkSomeNodesDead(args)
        elif notifyType == 'NodeProtocolInfo':
            self._handleNodeLinked(args)
        elif notifyType == 'EssentialNodeQueriesComplete':
            self._handleNodeReadyToMsg(args)
        elif notifyType == 'PollingDisabled':
            self._handlePollingDisabled(args)
        elif notifyType == 'PollingEnabled':
            self._handlePollingEnabled(args)
        elif notifyType == 'NodeNaming':
            self._handleNodeNaming(args)
        elif notifyType == 'NodeQueriesComplete':
            self._handleNodeQueryComplete(args)
        elif notifyType == 'Notification':
            self._handleNotification(args)
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
        self._timeStarted = time.time()
        self._log.info("Driver %s ready. homeId is 0x%0.8x, controller node id is %d, using %s library version %s", self._device,  self._homeId, self._activeNodeId, self._libraryTypeName, self._libraryVersion)
        self._log.info('OpenZWave Initialization Begins.')
        self.serverUI.broadcastMessage({'node': 'controller', 'type': 'driver-ready', 'usermsg' : 'Driver is ready.', 'data': True})
        self._cb_send_xPL({'type':'xpl-trig', 'schema':'ozwctrl.basic',
                                       'data': {'type': 'status', 'device': self._getCtrlDeviceName(), 'status':'init...'}})
        print ('controleur prêt' )

    def _handleNodeLinked(self, args):
        """Le node est relier au controleur."""
        node = self._getNode(self._homeId, args['nodeId'])
        if node :
            node.setLinked()
            self._log.info('Z-Wave Device Node {0} is linked to controller.'.format(node.id))        
        else :
            self._log.debug('Error notification : ', args)

    def _handleNodeReadyToMsg(self, args):
        """Les requettes essentielles d'initialisation du node sont complétée il peut recevoir des msg."""
        node = self._getNode(self._homeId, args['nodeId'])
        if node :
            node.setReceiver()
            self._log.info('Z-Wave Device Node {0} status essential queries ok.'.format(node.id))
            if node.id == self._ctrlnodeId and not self._ready :
                self._ready = True
                print ('controleur node ready pour autorisation dialogue UI')
                self._log.info('Z-Wave Controller Node {0} is ready, UI dialogue autorised.'.format(node.id))
        else :
            self._log.debug('Error notification : ', args)
       
    def _handleNodeNaming(self, args):
        """Le node à été identifié dans la lib openzwave. Son fabriquant et type sont connus"""
        node = self._getNode(self._homeId, args['nodeId'])
        if node :
            node.setNamed()
            self._log.info('Z-Wave Device Node {0} type is known in openzwave library.'.format(node.id))
            print ('Z-Wave Device Node {0} type is known in openzwave library.'.format(node.id))
        else :
            self._log.debug('Error notification : ', args)
        
    def _handleNodeQueryComplete(self, args):
        """Les requettes d'initialisation du node sont complété."""
        node = self._getNode(self._homeId, args['nodeId'])
        if node :
            node.setReady()
            node.updateNode()
            self._log.info('Z-Wave Device Node {0} is ready, full initialized.'.format(node.id))
            if node.id == self._ctrlnodeId and not self._ready :
                self._ready = True
                print ('controleur node ready pour autorisation dialogue UI')
                self._log.info('Z-Wave Controller Node {0} is ready, UI dialogue autorised.'.format(node.id))
        else :
            if args['nodeId'] == 255 and not self._ready :
                self._handleInitializationComplete(args) # TODO :depuis la rev 585 pas de 'AwakeNodesQueried' ou  'AllNodesQueried' ? on force l'init
    
    def _handleMarkSomeNodesDead(self,  args):
        """Un ou plusieurs node(s) ont été identifié comme mort"""
        self._log.info("Some nodes ares dead : " , args)
        print "**************************************"
        print ("Some nodes ares dead : " , args)
        # TODO: nouvelle notification à identifier et gérer le fonctionnement
            
    def _handleNotification(self,  args):
        """Une erreur ou notification particulière est arrivée
        NotificationCode
			Code_MsgComplete = 0,					/**< Completed messages */
			Code_Timeout,						/**< Messages that timeout will send a Notification with this code. */
			Code_NoOperation,					/**< Report on NoOperation message sent completion  */
			Code_Awake,						/**< Report when a sleeping node wakes up */
			Code_Sleep,						/**< Report when a node goes to sleep */
			Code_Dead,						/**< Report when a node is presumed dead */
			Code_Alive						/**< Report when a node is revived */
        """
        node = self._getNode(self._homeId, args['nodeId'])
        nCode = libopenzwave.PyNotificationCodes[args['notificationCode']]
        print nCode,  nCode.doc
        if not node:
            self._log.debug("Notification for node who doesn't exist : {0}".format(args))
        else :
            if nCode == 'MsgComplete':     #      Code_MsgComplete = 0,                                   /**< Completed messages */
                print 'MsgComplete notification code :', args
                self._log.debug('MsgComplete notification code for Node {0}.'.format(node.id))
                node.receivesCompletMsg(args)
            elif nCode == 'Timeout':         #      Code_Timeout,                                              /**< Messages that timeout will send a Notification with this code. */
                print 'Timeout notification on node :',  args['nodeId']
                self._log.info('Timeout notification code for Node {0}.'.format(args['nodeId']))
            elif nCode == 'NoOperation':  #       Code_NoOperation,                                       /**< Report on NoOperation message sent completion  */
                print 'NoOperation notification code :', args
                self._log.info('Z-Wave Device Node {0} successful receipt testing message.'.format(node.id))
                node.receivesNoOperation(args,  self.lastTest)
            elif nCode == 'Awake':            #      Code_Awake,                                                /**< Report when a sleeping node wakes up */
                node.setSleeping(False)
                print ('Z-Wave sleeping device Node {0} wakes up.'.format(node.id))
                self._log.info('Z-Wave sleeping device Node {0} wakes up.'.format(node.id))
            elif nCode == 'Sleep':            #      Code_Sleep,                                                /**< Report when a node goes to sleep */
                node.setSleeping(True)
                node.receiveSleepState(args)
                print ('Z-Wave Device Node {0} goes to sleep.'.format(node.id))
                self._log.info('Z-Wave Device Node {0} goes to sleep.'.format(node.id))
            elif nCode == 'Dead':             #       Code_Dead                                               /**< Report when a node is presumed dead */
                node.markAsFailed()
                print ('Z-Wave Device Node {0} marked as dead.'.format(node.id))
                self._log.info('Z-Wave Device Node {0} marked as dead.'.format(node.id))
            elif nCode == 'Alive':             #       Code_Alive						/**< Report when a node is revived */
                node.markAsOK()
                print ('Z-Wave Device Node {0} marked as alive.'.format(node.id))
                self._log.info('Z-Wave Device Node {0} marked as alive.'.format(node.id))
            else :
                self._log.error('Error notification code unknown : ', args)
            
    def _getNode(self, homeId, nodeId):
        """ Renvoi l'objet node correspondant"""
        if self._nodes.has_key(nodeId) :
            return self._nodes[nodeId] 
        else :
            print "Z-Wave Device Node {0} isn't register to manager.".format(nodeId)
            self._log.debug("Z-Wave Device Node {0} isn't register to manager.".format(nodeId))        
            return None
            
    def _fetchNode(self, homeId, nodeId):
        """ Renvoi et construit un nouveau node s'il n'existe pas et l'enregistre dans le dict """
        retval = self._getNode(homeId, nodeId)
        if retval is None:
            if nodeId != 0 :
                if nodeId == self._ctrlnodeId :
                    if not self._controller : 
                        retval = ZWaveController(self,  homeId, nodeId,  True)
                        print 'Node %d is affected as primary controller' % (nodeId)
                        self._log.info("Node %d is affected as primary controller)", nodeId)
                        self._controller = retval
                        self._controller.reportChangeToUI({'node': 'controller', 'type': 'init-process', 'usermsg' : 'Zwave network initialization process could take several minutes. ' +
                                                    ' Please be patient...', 'data': NodeStatusNW[3]})
                    else :
                        self._log.info("A primary controller allready existing, node %d id affected as secondary.", nodeId)
                        retval = ZWaveController(self,  homeId, nodeId,  False)
                else : 
                    retval = ZWaveNode(self,  homeId, nodeId)
                print 'Created new node with homeId 0x%0.8x, nodeId %d' % (homeId, nodeId)
                self._log.info('Created new node with homeId 0x%0.8x, nodeId %d', homeId, nodeId)
                self._nodes[nodeId] = retval
            else :
                self._log.debug("Can't create a Node ID n°0")
                raise OZwaveManagerException ("Can't create a Node ID n°0")
                retval = None
        return retval

    def _handlePollingDisabled(self, args):
        """le polling d'une value commande classe à été désactivé."""
        self._log.info('Node {0} polling disabled.'.format(args['nodeId']))
        data = {'polled': False}
    #    data['id'] = str(args['valueId']['id'])
        self.serverUI.broadcastMessage({'node': args['nodeId'], 'notifytype': 'polling', 'usermsg' : 'Polling disabled.', 'data': data})
        
    def _handlePollingEnabled(self, args):
        """le polling d'une value commande classe à été activé."""
        self._log.info('Node {0} polling enabled.'.format(args['nodeId']))
        data = {'polled': True}
     #   data['id'] = str(args['valueId']['id'])
        self.serverUI.broadcastMessage({'node': args['nodeId'], 'notifytype': 'polling', 'usermsg' : 'Polling enabled.', 'data': data})

    def _handleNodeChanged(self, args):
        """Un node est ajouté ou a changé"""
        node = self._fetchNode(args['homeId'], args['nodeId'])
        node._lastUpdate = time.time()
        self._log.info ('Node %d as add or changed (homeId %.8x)' , args['nodeId'],  args['homeId'])
        
    def _handleNodeRemoved(self, args):
        """Un node est ajouté ou a changé"""
        node = self._getNode(args['homeId'], args['nodeId'])
        if node :
            self._nodes.pop(node.id)
      #      node.__del__()
            self._log.info ('Node %d is removed (homeId %.8x)' , args['nodeId'],  args['homeId'])
            print ('Node %d is removed (homeId %.8x)' , args['nodeId'],  args['homeId'])
        else :
            self._log.debug ("Node %d unknown, isn't removed (homeId %.8x)" , args['nodeId'],  args['homeId'])

    def _handleValueAdded(self, args):
        """Un valueNode est ajouté au node depuis le réseaux zwave"""
        homeId = args['homeId']
        activeNodeId = args['nodeId']
        valueId = args['valueId']
        node = self._fetchNode(homeId, activeNodeId)
        node._lastUpdate = time.time()
        node.createValue(valueId)
       
    def _handleValueRemoved(self, args):
        """Un valueNode est retiré au node depuis le réseaux zwave"""
        homeId = args['homeId']
        activeNodeId = args['nodeId']
        valueId = args['valueId']
        node = self._fetchNode(homeId, activeNodeId)
        node._lastUpdate = time.time()
        node.removeValue(valueId)
       
    def _handleValueChanged(self, args):
        """"Un valuenode à changé sur le réseaux zwave"""
        sendxPL = False
        homeId = args['homeId']
        activeNodeId= args['nodeId']
        valueId = args['valueId']
        node = self._fetchNode(homeId, activeNodeId)
        node._lastUpdate = time.time()
        valueNode = node.getValue(valueId['id'])
        valueNode.updateData(valueId)
        # formattage infos générales
        # ici l'idée est de passer tout les valeurs stats et trig en identifiants leur type par le label forcé en minuscule.
        # les labels sont listés dans les tableaux des devices de la page spéciale, il faut les saisir dans sensor.basic-ozwave.xml.
        # Le traitement pour chaque command_class s'effectue danqs la ValueNode correspondante.
        msgtrig = valueNode.valueToxPLTrig()
        if msgtrig : self._cb_sendxPL_trig(msgtrig)
        else : print ('commande non  implémentee vers xPL : %s'  % valueId['commandClass'] )

    def _handleNodeEvent(self, args):
        """Un node à envoyé une Basic_Set command  au controlleur.  
        Cette notification est générée par certains capteur,  comme les decteurs de mouvement type PIR, pour indiquer qu'un événements a été détecter.
        Elle est aussi envoyée dans le cas d'une commande locale d'un device. """
  #     CmdsClassBasicType = ['COMMAND_CLASS_SWITCH_BINARY', 'COMMAND_CLASS_SENSOR_BINARY', 'COMMAND_CLASS_SENSOR_MULTILEVEL', 
  #                                           'COMMAND_CLASS_SWITCH_MULTILEVEL',  'COMMAND_CLASS_SWITCH_ALL',  'COMMAND_CLASS_SWITCH_TOGGLE_BINARY',  
  #                                           'COMMAND_CLASS_SWITCH_TOGGLE_MULTILEVEL', 'COMMAND_CLASS_SENSOR_MULTILEVEL', ]
        sendxPL = False
        homeId = args['homeId']
        activeNodeId = args['nodeId']
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
                valuebasic[0].valueData['value'] = valuebasic[0].convertInType(args['event'])
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
        """La séquence d'initialisation du controlleur zwave est terminée."""
        controllercaps = set()
        if self._manager.isPrimaryController(self._homeId): controllercaps.add('Primary Controller')
        if self._manager.isStaticUpdateController(self._homeId): controllercaps.add('Static Update Controller')
        if self._manager.isBridgeController(self._homeId): controllercaps.add('Bridge Controller')
        self._controllerCaps = controllercaps
        self._log.info('Controller capabilities are: %s', controllercaps)
        for node in self._nodes.values():  
            node.updateNode() # Pourrait être utile si un node s'est réveillé pendant l'init
            node._updateConfig()
        self._ready = True
        self._initFully = True
        self._controller.reportChangeToUI({'node': 'controller', 'type': 'init-process', 'usermsg' : 'Zwave network Initialized.', 'data': NodeStatusNW[2]})
        self._cb_send_xPL({'type':'xpl-trig', 'schema':'ozwctrl.basic',
                                    'data': {'type': 'status', 'device': self._getCtrlDeviceName(), 'status':'ok'}})
        print ("OpenZWave initialization is complete.  Found {0} Z-Wave Device Nodes ({1} sleeping)".format(self.nodeCount, self.sleepingNodeCount))
        self._log.info("OpenZWave initialization is complete.  Found {0} Z-Wave Device Nodes ({1} sleeping)".format(self.nodeCount, self.sleepingNodeCount))
        #self._manager.writeConfig(self._homeId)

    def _handleGroupChanged(self, args):
        """Report de changement d'association au seins d'un groupe"""
        node = self._fetchNode(args['homeId'], args['nodeId'])
        node.updateGroup(args['groupIdx'])
         
    def getCommandClassName(self, commandClassCode):
        """Retourn Le nom de la commande class en fonctionde son code."""
        return PyManager.COMMAND_CLASS_DESC[commandClassCode]

    def getCommandClassCode(self, commandClassName):
        """Retourn Le code de la command class en fonction de son nom."""
        for k, v in PyManager.COMMAND_CLASS_DESC.iteritems():
            if v == commandClassName:
                return k
        return None
        
    def handle_ControllerAction(self,  action):
        """Transmet une action controlleur au controlleur primaire."""
        print ('********************** handle_ControllerAction ***********')
        print 'Action : ',  action
        if self._controller :
            self._ctrlActProgress = action   
            retval = self._controller.handle_Action(action)
        else :
            self._ctrlActProgress = None
            retval = action
            retval.update({'cmdstate': 'not running' , 'error': 'not controller', 'error_msg': 'Check your controller.'})
        return retval    
        
    def  handle_ControllerSoftReset(self):
        """Transmmet le soft resset au controlleur primaire."""
        retval = {'error': ''}
        if not self._controller.soft_reset() :
            retval['error'] = 'No reset for secondary controller'
        return retval
        
    def  handle_ControllerHardReset(self):
        """Transmmet le hard resset au controlleur primaire."""
        retval = {'error': ''}
        if not self._controller.hard_reset() :
            retval['error'] = 'No reset for secondary controller'
        return retval
    
    def getCountMsgQueue(self):
        """"Retourne le nombre de message
        :return: The count of messages in the outgoing send queue.
        :rtype: int
        """
        return self._manager.getSendQueueCount(self.homeId)
        
    def getNetworkInfo(self):
        """ Retourne les infos principales du réseau zwave (dict) """
        retval = {}
        retval["ConfigPath"] = self._configPath
        retval["UserPath"] = self._userPath
        retval["PYOZWLibVers"] = self.pyOZWLibVersion
        retval["OZWPluginVers"] = OZWPLuginVers
        if self.ready :
            retval["HomeID"] ="0x%.8x" % self.homeId
            retval["Model"] = self.controllerNode.manufacturer + " -- " + self.controllerNode.product
            retval["Protocol"] = self._manager.getControllerInterfaceType(self.homeId)
            retval["Primary controller"] = self.controllerDescription
            retval["Device"] = self.device
            retval["Node"] = self.controllerNode.nodeId
            retval["Library"] = self._libraryTypeName
            retval["Version"] = self._libraryVersion
            retval["Node count"] = self.nodeCount
            retval["Node sleeping"] = self.sleepingNodeCount
            retval['Poll interval'] = self._controller.getPollInterval()
            if self._initFully :
                retval["Init state"] = NodeStatusNW[2] #Completed
            else :
                retval["Init state"] = NodeStatusNW[3] #In progress - Devices initializing
            retval["error"] = ""
            ln = []
            for n in self.nodes : ln.append(n)
            retval["ListNodeId"] = ln
            print'**** getNetworkinfo : ',  retval
            return retval
        else : 
            retval["error"] = "Zwave network not ready, be patient..."
            retval["Init state"] = NodeStatusNW[0] #Uninitialized
            return retval
        
    def saveNetworkConfig(self):
        """Enregistre le configuration au format xml"""
        retval = {}
        self._manager.writeConfig(self.homeId)
        print "config sauvée"
        retval["File"] = "confirmed"
        return retval

    def getZWRefFromxPL(self, device):
        """ Retourne  les références Zwave envoyées depuis le xPL domogik 
        @ param : device format : nomReseaux.NodeID.Instance """
        ids = device.split('.')
        retval = {}
        retval['homeId'] = self._nameAssoc[ids[0]] if self._nameAssoc[ids[0]]  else self.homeId
        if (retval['homeId'] == 0) : retval['homeId'] = self.homeId # force le homeid si pas configuré correctement, TODO: gérer un message pour l'utilisateur pour erreur de config.
        retval['nodeId']  = int(ids[1])
        retval['instance']  = int(ids[2])
        print "getZWRefFromxPL : ", retval
        return retval
        
    def sendNetworkZW(self, command,  device, opt =""):
        """ En provenance du réseaux xPL
              Envoie la commande sur le réseaux zwave  """ 
        print ("envoi zwave command %s" % command)
        if device != None :
            addrZW = self.getZWRefFromxPL(device)
            nodeId = int(addrZW['nodeId'])
            homeId = addrZW['homeId'] # self.homeId
            instance = addrZW['instance']
            node = self._getNode(homeId,  nodeId)
            if node : node.sendCmdBasic(instance, command, opt)

    def getNodeInfos(self,  nodeId):
        """ Retourne les informations d'un device, format dict{} """
        if self.ready :
            node = self._getNode(self.homeId,  nodeId)
            if node : return node.getInfos()
            else : return {"error" : "Unknown Node : %d" % nodeId}
        else : return {"error" : "Zwave network not ready, can't find node %d" % nodeId}
        
    def refreshNodeDynamic(self,  nodeId):
        """ Force un rafraichissement des informations du node depuis le reseaux zwave"""
        if self.ready :
            node = self._getNode(self.homeId,  nodeId)
            if node : return node.requestNodeDynamic()
            else : return {"error" : "Unknown Node : %d" % nodeId}
        else : return {"error" : "Zwave network not ready, can't find node %d" % nodeId}
        
    def refreshNodeInfo(self,  nodeId):
        """ Force un rafraichissement des informations du node depuis le reseaux zwave"""
        if self.ready :
            node = self._getNode(self.homeId,  nodeId)
            if node : return node.requestNodeInfo()
            else : return {"error" : "Unknown Node : %d" % nodeId}
        else : return {"error" : "Zwave network not ready, can't find node %d" % nodeId}
        
    def refreshNodeState(self,  nodeId):
        """ Force un rafraichissement des informations primaires du node depuis le reseaux zwave"""
        if self.ready :
            node = self._getNode(self.homeId,  nodeId)
            if node : return node.requestNodeState()
            else : return {"error" : "Unknown Node : %d" % nodeId}
        else : return {"error" : "Zwave network not ready, can't find node %d" % nodeId}

    def getNodeValuesInfos(self,  nodeId):
        """ Retourne les informations de values d'un device, format dict{} """
        retval = {}
        if self.ready :
            node = self._getNode(self.homeId,  nodeId)
            if node : return node.getValuesInfos()
            else : return {"error" : "Unknown Node : %d" % nodeId}
        else : return {"error" : "Zwave network not ready, can't find node %d" %nodeId}
        
    def getValueInfos(self,  nodeId,  valueId):
        """ Retourne les informations d'une value d'un device, format dict{} """
        retval = {}
        if self.ready :
            node = self._getNode(self.homeId,  nodeId)
            if node :
                value = node.getValue(valueId)
                if value :
                    retval = value.getInfos()
                    retval['error'] = ""
                    return retval
                else : return {"error" : "Unknown value : %d" % valueId}
            else : return {"error" : "Unknown Node : %d" % nodeId}
        else : return {"error" : "Zwave network not ready, can't find value %d" % valueId}
        
    def getValueTypes(self):
        """Retourne la liste des type de value possible et la doc"""
        retval = {}
        for elem in  libopenzwave.PyValueTypes :
            retval[elem] = elem.doc
        return retval
        
    def getListCmdsCtrl(self):
        """Retourne le liste des commandes possibles du controleur ainsi que la doc associée."""
        retval = {}
        if self.ready :
            retval = self._controller.cmdsAvailables()
            retval['error'] = ""
            return retval
        else : return {"error" : "Zwave network not ready, can't find controller."}

    def testNetwork(self, count = 1, timeOut = 10000,  allReport = False):
        """Envois une serie de messages à tous les nodes pour tester la réactivité du réseaux."""
        retval = {'error': ''}
        if self.ready :
            for i in self._nodes :
                n = self._nodes[i]
                if not n.isSleeping and n != self._controller :
                    error = n.trigTest(count, timeOut,  allReport,  False)
                    if error['error'] != '' :  retval['error'] = retval['error'] +'/n' + error['error']
            self.lastTest = time.time()
            self._manager.testNetwork(self.homeId, count)
            if retval['error']  != '': retval['error'] = 'Some node(s) have error :/n' + retval['error']
            return retval
        else : return {"error" : "Zwave network not ready, can't find controller."}

    def testNetworkNode(self, nodeId, count = 1, timeOut = 10000,  allReport = False):
        """Envois une serie de messages à un node pour tester sa réactivité sur le réseaux."""
        retval = {}
        if self.ready :
            node = self._getNode(self.homeId,  nodeId)
            if node != self._controller  :
                if node : retval = node.testNetworkNode(count, timeOut,  allReport)
                else : retval['error'] = "Zwave node %d unknown." %nodeId
            else : retval['error'] = "Can't test primary controller, node %d." %nodeId
            return retval
        else : return {"error" : "Zwave network not ready, can't find node %d" % nodeId}
    
    def healNetwork(self, homeId, upNodeRoute):
        """Tente de 'réparé' des nodes pouvant avoir un problème. Passe tous les nodes un par un"""
        if self.ready :
            self._manager.healNetwork(homeId, upNodeRoute)

    def healNetworkNode(self, homeId, nodeId,  upNodeRoute):
        """Tente de 'réparé' un node particulier pouvant avoir un problème."""
        if self.ready :
            node = self._getNode(homeId,  nodeId)
            if node : self._manager.healNetworkNode(homeId, nodeId,  upNodeRoute)
        
    def getGeneralStatistics(self):
        """Retourne les statistic générales du réseaux"""
        retval={}
        if self.ready :
            retval = self._controller.stats()
            if retval : 
                for  item in retval : retval[item] = str (retval[item]) # Pour etre compatible avec javascript
                retval['error'] = ""
            else : retval = {'error' : "Zwave controller not response."}
            retval['msqueue'] = str(self.getCountMsgQueue())
            retval['elapsedtime'] = str(timedelta(0,time.time()-self._timeStarted))
            return retval
        else : return {"error" : "Zwave network not ready, can't find controller"}        

    def getNodeStatistics(self, nodeId):
        """Retourne les statistic d'un node"""
        retval = {}
        if self.ready :
            node = self._getNode(self.homeId,  nodeId)
            if node :
                retval = node.getStatistics()
                if retval : 
                    retval['error'] = ""
                    for item in retval['ccData'] :
                        item['commandClassId']  = self.getCommandClassName(item['commandClassId'] ) + ' (' + hex(item['commandClassId'] ) +')'
                else : retval = {'error' : "Zwave node %d not response." %nodeId}
            else : retval['error'] = "Zwave node %d unknown" %nodeId
            return retval
        else : return {"error" : "Zwave network not ready, can't find node %d" % nodeId}

    def setUINodeNameLoc(self,  nodeId,  newname, newloc):
        """Change le nom et/ou le localisation du node dans OZW et dans le decive si celui-ci le supporte """
        if self.ready :
            node = self._getNode(self.homeId,  nodeId)
            if newname != 'Undefined' and node.name != newname :
                try :
                    node.setName(newname)
                except Exception as e:
                    self._log.error('node.setName() :' + e.message)
                    return {"error" : "Node %d, can't update name, error : %s" %(nodeId, e.message) }
            if newloc != 'Undefined' and node.location != newloc :
                try :
                    node.setLocation(newloc)
                except Exception as e:
                    self._log.error('node.setLocation() :' + e.message)
                    return {"error" : "Node %d, can't update location, error : %s" %(nodeId, e.message) }
            return node.getInfos()                                
        else : return {"error" : "Zwave network not ready, can't find node %d" %nodeId}

    def setValue(self,  nodeId,  valueId,  newValue):
        """Envoie la valeur a l'objet value"""
        retval = {}
        if self.ready :
            node = self._getNode(self.homeId,  nodeId)
            if node :
                value = node.getValue(valueId)
                if value :
                    retval = value.setValue(newValue)
              #      print ('SetValue, relecture de la valeur : ',  value.getOZWValue())
                    return retval
                else : return {"value": newValue, "error" : "Unknown value : %d" %valId}
            else : return {"error" : "Unknown Node : %d" % nodeId}
        else : return {"value": newValue, "error" : "Zwave network not ready, can't find value %d" %valId}     

    def setMembersGrps(self,  nodeId,  newGroups):
        """Envoie les changement des associations de nodes dans les groups d'association."""
        retval = {}
        if self.ready :
            node = self._getNode(self.homeId,  nodeId)
            if node :
                grp =node.setMembersGrps(newGroups)
                if grp :
                    retval['groups'] = grp
                    retval['error'] = ""
                    return retval
                else : return {"error" : "Manager not send association changement on node %d." %nodeId}
                return retval
            else : return {"error" : "Unknown Node : %d" % nodeId}
        else : return {"error" : "Zwave network not ready, can't find node %d" % nodeId}
    
    def _IsNodeId(self, nodeId):
        """Verifie le si le format de nodeId est valide"""
        return True if (type(nodeId) == type(0) and (nodeId >0 and nodeId < 255)) else False
    
    def cb_ServerWS(self, message):
        """Callback en provenance de l'UI via server Websocket (resquest avec ou sans ack)"""
        blockAck = False
        report = {'error':  'Message not handle.'}
        ackMsg = {}
        print "WS - Requete UI",  message
        if message.has_key('header') :
            if message['header']['type'] in ('req', 'req-ack'):
                if message['request'] == 'ctrlAction' :
                    report = self.handle_ControllerAction(message['action'])
             #       if message['action']['cmd'] =='getState' and report['cmdstate'] != 'stop' : blockAck = True
                elif message['request'] == 'ctrlSoftReset' :
                    report = self.handle_ControllerSoftReset()
                elif message['request'] == 'ctrlHardReset' :
                    report = self.handle_ControllerHardReset()
                elif message['request'] == 'GetNetworkID' :
                    report = self.getNetworkInfo()
                elif message['request'] == 'GetNodeInfo' :
                    if self._IsNodeId(message['node']):
                        report = self.getNodeInfos(message['node'])
                    else : report = {'error':  'Invalide nodeId format.'}
                    ackMsg['node'] = message['node']
                    print "Refresh node :", report
                elif message['request'] == 'RefreshNodeDynamic' :
                    if self._IsNodeId(message['node']):
                        report = self.refreshNodeDynamic(message['node'])
                    else : report = {'error':  'Invalide nodeId format.'}
                    ackMsg['node'] = message['node']
                elif message['request'] == 'RefreshNodeInfo' :
                    if self._IsNodeId(message['node']):
                        report = self.refreshNodeInfo(message['node'])
                    else : report = {'error':  'Invalide nodeId format.'}
                    ackMsg['node'] = message['node']
                elif message['request'] == 'RefreshNodeState' :
                    if self._IsNodeId(message['node']):
                        report = self.refreshNodeState(message['node'])
                    else : report = {'error':  'Invalide nodeId format.'}
                    ackMsg['node'] = message['node']
                    print "Refresh node :", report
                elif message['request'] == 'HealNode' :
                    if self._IsNodeId(message['node']):
                        self.healNetworkNode(self.homeId,  message['node'],  message['forceroute'])
                        report = {'usermsg':'Command sended, please wait for result...'}
                    else : report = {'error':  'Invalide nodeId format.'}
                    ackMsg['node'] = message['node']
                elif message['request'] == 'HealNetwork' :
                    self.healNetwork(self.homeId, message['forceroute'])
                    report = {'usermsg':'Command sended node by node, please wait for each result...'}
                elif message['request'] == 'SaveConfig':
                    report = self.saveNetworkConfig()
                elif message['request'] == 'GetMemoryUsage':
                    report = self.getMemoryUsage()
                elif message['request'] == 'GetAllProducts':
                    report = self.getAllProducts()
                elif message['request'] == 'SetNodeNameLoc':
                    report = self.setUINodeNameLoc(message['node'], message['newname'],  message['newloc'])
                    ackMsg['node'] = message['node']
                elif message['request'] == 'GetNodeValuesInfo':
                    if self._IsNodeId(message['node']):
                        report =self.getNodeValuesInfos(message['node'])
                    else : report = {'error':  'Invalide nodeId format.'}
                    ackMsg['node'] = message['node']
                elif message['request'] == 'GetValueInfos':
                    if self._IsNodeId(message['node']):
                        valId = long(message['valueid']) # Pour javascript type string
                        report =self.getValueInfos(message['node'], valId)
                    else : report = {'error':  'Invalide nodeId format.'}
                    ackMsg['node'] = message['node']
                    ackMsg['valueid'] = message['valueid']
                    print 'Refresh one Value infos : ', report
                elif message['request'] == 'SetPollInterval':
                    self._controller.setPollInterval(message['interval'],  False)
                    ackMsg['interval'] = self._controller.getPollInterval()
                    if  ackMsg['interval'] == message['interval']:
                        report = {'error':''}
                    else :
                        report = {'error':'Setting interval error : keep value %d ms.' %ackMsg['interval']}
                elif message['request'] == 'EnablePoll':
                    valId = long(message['valueid']) # Pour javascript type string
                    report = self._controller.enablePoll( message['node'],  valId,  message['intensity'])
                    ackMsg['node'] = message['node']
                    ackMsg['valueid'] = message['valueid']
                elif message['request'] == 'DisablePoll':
                    valId = long(message['valueid']) # Pour javascript type string
                    report = self._controller.disablePoll( message['node'],  valId)
                    ackMsg['node'] = message['node']
                    ackMsg['valueid'] = message['valueid']
    
                elif message['request'] == 'GetValueTypes':
                    report = sGetListCmdsCtrlelf.getValueTypes()  
                elif message['request'] == 'GetListCmdsCtrl':
                    report = self.getListCmdsCtrl()
                elif message['request'] == 'setValue':
                    if self._IsNodeId(message['node']):
                        valId = long(message['valueid']) # Pour javascript type string
                        report = self.setValue(message['node'], valId, message['newValue'])
                    else : report = {'error':  'Invalide nodeId format.'}
                    ackMsg['node'] = message['node']
                    ackMsg['valueid'] = message['valueid']
                    print 'Set command_class Value : ',  report
                elif message['request'] == 'setGroups':
                    if self._IsNodeId(message['node']):
                        report = self.setMembersGrps(message['node'], message['ngrps'])
                    else : report = {'error':  'Invalide nodeId format.'}
                    ackMsg['node'] = message['node']         
                    print 'Set Groups association : ',  report
                elif message['request'] == 'GetGeneralStats':
                    report = self.getGeneralStatistics()
                    print 'Refresh generale stats : ',  report                
                elif message['request'] == 'GetNodeStats':
                    if self._IsNodeId(message['node']):
                        report = self.getNodeStatistics(message['node'])
                    else : report = {'error':  'Invalide nodeId format.'}
                    ackMsg['node'] = message['node']
                    print 'Refresh node stats : ',  report
                elif message['request'] == 'StartCtrl':
                    if not self.ready : 
                        self.openDevice(self.device)
                        report = {'error':'',  'running': True}
                    else : report = {'error':'Driver already running.',  'running': True}
                    print 'Start Driver : ',  report
                elif message['request'] == 'StopCtrl':
                    if self.device and self._ctrlnodeId : 
                        self.closeDevice(self.device)
                        report = {'error':'',  'running': False}
                    else : report = {'error':'No Driver knows.',  'running': False}
                    print 'Stop Driver : ',  report
                elif message['request'] == 'TestNetwork':
                    report = self.testNetwork(message['count'],  10000, True)
                elif message['request'] == 'TestNetworkNode':
                    if self._IsNodeId(message['node']):
                        report = self.testNetworkNode(message['node'],  message['count'],  10000, True)
                    else : report = {'error':  'Invalide nodeId format.'}
                    ackMsg['node'] = message['node']
                elif message['request'] == 'GetLog':
                    report = self.getLoglines(message)
                elif message['request'] == 'GetLogOZW':
                    report = self.getLogOZWlines(message)
                elif message['request'] == 'StartMonitorNode':
                    if self._IsNodeId(message['node']):
                        report = self.monitorNodes.startMonitorNode(message['node'])
                    else : report = {'error':  'Invalide nodeId format.'}
                    ackMsg['node'] = message['node']
                elif message['request'] == 'StopMonitorNode':
                    if self._IsNodeId(message['node']):
                        report = self.monitorNodes.stopMonitorNode(message['node'])
                    else : report = {'error':  'Invalide nodeId format.'}
                    ackMsg['node'] = message['node']
                else :
                    report['error'] ='Unknown request.'
                    print "commande inconnue"
            if message['header']['type'] == 'req-ack' and not blockAck :
                ackMsg['header'] = {'type': 'ack',  'idws' : message['header']['idws'], 'idmsg' : message['header']['idmsg'],
                                               'ip' : message['header']['ip'] , 'timestamp' : long(time.time()*100)}
                ackMsg['request'] = message['request']
                if report :
                    if 'error' in report :
                        ackMsg['error'] = report['error']
                    else :
                        ackMsg['error'] = ''
                    ackMsg['data'] = report
                else : 
                    ackMsg['error'] = 'No data report.'
                self.serverUI.sendAck(ackMsg)
        else :
            raise OZwaveManagerException("WS request bad format : {0}".format(message))

                
    def reportCtrlMsg(self, ctrlmsg):
        """Un message de changement d'état a été recu, il est reporté au besoin sur le hub xPL pour l'UI
            SIGNAL_CTRL_NORMAL = 'Normal'                   # No command in progress.  
            SIGNAL_CTRL_STARTING = 'Starting'             # The command is starting.  
            SIGNAL_CTRL_CANCEL = 'Cancel'                   # The command was cancelled.
            SIGNAL_CTRL_ERROR = 'Error'                       # Command invocation had error(s) and was aborted 
            SIGNAL_CTRL_WAITING = 'Waiting'                # Controller is waiting for a user action.  
            SIGNAL_CTRL_SLEEPING = 'Sleeping'              # Controller command is on a sleep queue wait for device.  
            SIGNAL_CTRL_INPROGRESS = 'InProgress'       # The controller is communicating with the other device to carry out the command.  
            SIGNAL_CTRL_COMPLETED = 'Completed'         # The command has completed successfully.  
            SIGNAL_CTRL_FAILED = 'Failed'                     # The command has failed.  
            SIGNAL_CTRL_NODEOK = 'NodeOK'                   # Used only with ControllerCommand_HasNodeFailed to indicate that the controller thinks the node is OK.  
            SIGNAL_CTRL_NODEFAILED = 'NodeFailed'       # Used only with ControllerCommand_HasNodeFailed to indicate that the controller thinks the node has failed.
        """

        report  = {}
        if self._ctrlActProgress :
            report = self._ctrlActProgress
        else :            
            report['action'] = 'undefine'
            report['id'] = 0
            report['cmd'] = 'undefine'
            report['cptmsg'] = 0
            report['cmdSource'] = 'undefine'
            report['arg'] ={}
        report['state'] = ctrlmsg['state'] 
        report['error'] = ctrlmsg['error']
        report['message'] = ctrlmsg['message']
        if ctrlmsg['error_msg'] != 'None.' : report['err_msg'] = ctrlmsg['error_msg']  
        else : report['err_msg'] = 'no'
        report['update'] = ctrlmsg['update']
        print 'reportCtrlMsg', ctrlmsg
        if ctrlmsg['state'] == self._controller.SIGNAL_CTRL_FAILED :
            node = self._getNode(self._homeId, ctrlmsg['nodeid']) 
            if node : node.markAsFailed();
        if ctrlmsg['state'] == self._controller.SIGNAL_CTRL_NODEOK :
            node = self._getNode(self._homeId, ctrlmsg['nodeid']) 
            if node : node.markAsOK()
        if ctrlmsg['state'] in [self._controller.SIGNAL_CTRL_NORMAL,  self._controller.SIGNAL_CTRL_CANCEL,
                                        self._controller.SIGNAL_CTRL_ERROR,  self._controller.SIGNAL_CTRL_COMPLETED,  
                                        self._controller.SIGNAL_CTRL_FAILED, self._controller.SIGNAL_CTRL_NODEOK] :
            report['cmdstate'] = 'stop'                                            
            self._ctrlActProgress= None   
        else :
            report['cmdstate'] = 'waiting'
        msg = {'notifytype': 'ctrlstate'}
        msg['data'] = report
        self.serverUI.broadcastMessage(msg)
