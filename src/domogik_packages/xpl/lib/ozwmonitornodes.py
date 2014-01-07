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
@copyright: (C) 2007-2013 Domogik project
@license: GPL(v3)
@organization: Domogik
"""
import threading
from datetime import datetime
from ozwdefs import *
from collections import deque
import pprint
from tailer import Tailer

class OZwaveMonitorNodeException(OZwaveException):
    """"Zwave monitor node manager exception  class"""
            
    def __init__(self, value):
        OZwaveException.__init__(self, value)
        self.msg = "OZwave monitor node exception:"
        
class ManageMonitorNodes(threading.Thread):
    """Monitor Node manager"""
    
    def __init__(self, ozwManager):
        """Crée l'instance de surveillance de node(s)"""
        threading.Thread.__init__(self)
        self.name = "Manage_Monitor_Nodes"
        self._ozwManager = ozwManager
        self.nodesMonitor={}
        self.__reports =deque([])
        self._pluginLog = ozwManager._log
        self._stop = ozwManager._stop
        self._pluginLog.info('Monitor node(s) manager is initialized.')
    
    def run(self):
        """Tache en cours"""
        if self._ozwManager._ozwLog : 
            ozwfile = os.path.join(self._ozwManager._userPath + "OZW_Log.txt")
            if not os.path.isfile(ozwfile) : 
                self._pluginLog.info( "No existing openzwave log file : " + ozwfile + " Monitor Nodes don't monitor openzwave lib.")
            else :
                rOZW = MonitorOZW(self.logOZW_report,  ozwfile, self._stop,  self._pluginLog)
                rOZW.start()
        else : self._pluginLog.info( "No log activate for openzwave. Monitor Nodes don't monitor openzwave lib.")
        self._pluginLog.info('Monitor node(s) manager is started.')
        while not self._stop.isSet():
            if self.__reports :
                report = self.__reports.popleft()
                self.logNode(report['date'], report['type'],  report['nodeId'], report['datas'])
            else : self._stop.wait(0.01)
        # flush and close list nodes
        for node in self.nodesMonitor :
            self.nodesMonitor[node].close()
            del self.nodesMonitor[node]
        self._pluginLog.info('Monitor node(s) manager is stopped.')
        print 'Monitor node(s) manager is stopped.'

    def openzwave_report(self,  args):
        """Callback depuis la librairie py-openzwave 
        """
        if self.isMonitored(args['nodeId']) : 
            self.__reports.append({'date': datetime.now(),'type': "Openzwave Notification : " + args['notificationType'], 'nodeId': args['nodeId'], 'datas': args})
    
    def xpl_report(self,  xplMsg):
        """Callback un message Xpl"""
        if xplMsg.data.has_key('device') and xplMsg.data['device'] != None :
            try :
                zN,  nodeId,  instance = xplMsg.data['device'].split(".")
                nodeId = int(nodeId)
                if self.isMonitored(nodeId) : 
                    self.__reports.append({'date': datetime.now(),'type': "Xpl report : ", 'nodeId': nodeId, 'datas': str(xplMsg)})
            except Exception as e :
                raise OZwaveMonitorNodeException(e)
    #    else : self._pluginLog.debug("Monitoring nodes, No 'device' key defined in xPL msg ({0})".format(xplMsg))
            
    def nodeChange_report(self,  nodeId,  msg):
        """Callback de node lui même"""
        if self.isMonitored(nodeId) :
            if msg.has_key('header') : del msg['header']
            if msg.has_key('node') : del msg['node']
            if msg.has_key('ctrldevice') : del msg['ctrldevice']
            self.__reports.append({'date': datetime.now(),'type': "Node change report : ", 'nodeId': nodeId, 'datas': msg})
        
    def logOZW_report(self,  line):
        """Callback de surveillance du log openzwave"""
        idx = line.find('Node')
        if  idx != -1 : 
            try :
                nodeId = int(line[idx+4:idx+7])
                if self.isMonitored(nodeId) :
                    self.__reports.append({'date': datetime.now(),'type': "openzwave lib", 'nodeId': nodeId, 'datas': line})
            except :
                pass

    def nodeCompletMsg_report(self,  nodeId,  msg):
        """Callback de node lui même"""
        if self.isMonitored(nodeId) :
            if msg.has_key('header') : del msg['header']
            if msg.has_key('node') : del msg['node']
            if msg.has_key('ctrldevice') : del msg['ctrldevice']
            self.__reports.append({'date': datetime.now(),'type': "Node receive completed message : ", 'nodeId': nodeId, 'datas': msg})

    def isMonitored(self, nodeId):
        """Renvois True si le node est surveillé."""
        if int(nodeId) in self.nodesMonitor: 
            return True
        else:
            return False
    
    def getFileName(self,  nodeId):
        """Retourne le nom du fichier de log attendus"""
        node = '%03d' % nodeId 
        return self._ozwManager._userPath + "lognode"  + node +".log"
        
    def startMonitorNode(self, nodeId):
        """Demarre la surveillance du node dans un fichier log."""
        retval = {'error': ''}
        if not self.isMonitored(nodeId) :
            fName = self.getFileName(nodeId)
            fLog = open(fName,  "w")
            self._pluginLog.info('Start monitor node {0} in log file : {1}.'.format(nodeId,  fName))
            retval.update({'state': 'started','usermsg':'Start monitor node {0} in log file.'.format(nodeId), 'file': fName})
            fLog.write("{0} - Started monitor log for node {1}.\n".format(datetime.now(),  nodeId))
            node = self._ozwManager._getNode(self._ozwManager.homeId, nodeId)
            if node : 
                infos = node.getInfos()
                fLog.write("Node is registered in manager, state information : \n ")
                pprint.pprint(infos, stream=fLog)
                infos = node.getValuesInfos()
                pprint.pprint(infos, stream=fLog)
                fLog.write("===============================================\n")
            else :
                fLog.write("Node isn't registered in manager.\n")
            fLog.close()
            fLog = open(fName,  "a")  # reopen in append mode
            self.nodesMonitor.update({nodeId : fLog})
        else :
            retval.update({'state': 'started','usermsg': 'Monitor node {0} in log already started.'.format(nodeId), 'file': fName})
            self._pluginLog.debug('Monitor node {0} in log already started.'.format(nodeId))
        return retval
        
    def stopMonitorNode(self, nodeId):
        """Arrete la surveillance du node"""
        retval = {'error': ''}
        if self.isMonitored(nodeId) :
            fLog = self.nodesMonitor[nodeId]
            retval.update({'state': 'stopped','usermsg': 'Stop monitor node {0} in log file.'.format(nodeId), 'file': self.getFileName(nodeId)})
            self._pluginLog.info('Stop monitor node {0} in log file : {1}.'.format(nodeId,  self.getFileName(nodeId)))
            fLog.write("{0} - Stopped monitor log for node {1}.".format(datetime.now(),  nodeId))
            fLog.close()
            del self.nodesMonitor[nodeId]
        else :
            retval.update({'error': 'Monitor node {0} not running.'.format(nodeId)})
        return retval
            
    def logNode(self, date,  type, nodeId, args):
        """log les informations d'un node dans le fichier lognodeXXX.log de data/ozwave"""
        fLog = self.nodesMonitor[nodeId]
        if type == 'openzwave lib':
            fLog.write('{0}\n'.format(args))
        else :
            fLog.write("{0} - {1}\n".format(date,  type))
            if isinstance(args,  str) : fLog.write(args)
            else : 
                pprint.pprint(args, stream=fLog)
                fLog.write("-----------------------------------------------------------\n")
                
class MonitorOZW(threading.Thread):
    """Class for monitor openzwave log"""
    
    def __init__(self,  cb_logNode,  ozwlogfile,  stop,  pluginLog):
        """Crée l'instance de surveillance du log openzwave"""
        threading.Thread.__init__(self)
        self.name = "Manage_Monitor_Log Openzwave"
        self.cb_logNode = cb_logNode
        self.ozwlogfile = ozwlogfile
        self._stop = stop
        self._pluginLog = pluginLog
        self._pluginLog.info('Monitor openzwave manager is initialized.')
        self.running = False

    def run(self):
        """Démarre le thread d'écoute du log openzwave."""
        self._pluginLog.info('Monitor openzwave manager is started.')
        self.running = True
        ozwTail = Tailer(open(self.ozwlogfile,  'rb'))
        for line in ozwTail.follow(delay=0.01):
            if line : self.cb_logNode(line)
            if self._stop.isSet() or not self.running : break
        self.running = False
        self._pluginLog.info('Monitor openzwave manager is stopped.')
        
    def stop(self):
        """Stop le thread d'écoute du log openzwave au prochain log."""
        self.running = False
