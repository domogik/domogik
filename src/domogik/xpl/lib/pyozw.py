#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
import datetime
import sys

class ZwaveException(Exception):
    '''
    Zwave Exception
    '''

    def __init__(self, value):
        Exception.__init__(self)
        self.value = value

    def __str__(self):
        return repr(self.value)


class ZWave:
    """
    ZWave class
    """

    def __init__(self, serial_port, pyozw_path, callback):
        """initialisation serial port
        """
        self._cb = callback
        pyozw_dir = str(pyozw_path) + "/examples"
        pyozw_conf = str(pyozw_path) + "/openzwave/config/"
        sys.path.insert(0,pyozw_dir)
        from common.ozwWrapper import ZWaveWrapper, ZWaveNode, ZWaveValueNode
        self.w = ZWaveWrapper.getInstance(device=serial_port, config=pyozw_conf)
        print "\nPlease Wait during discover network..."
        while bool(self.w.initialized) != True:
            time.sleep(0.1)
            sys.stdout.write("*")
            sys.stdout.flush()
        time.sleep(0.5)
        while self.w.nodes[self.w.nodes.keys()[-1]].productType == '':
            time.sleep(0.1)
            sys.stdout.write("*")
            sys.stdout.flush()
        sys.stdout.write(" Initialised !\n")
        print " "
        print "Controller : " + str(self.w.controllerDescription) + " on " + str(serial_port )
        print "Home ID : " + str(self.w.homeId)
        print "Registered Nodes : " + str(self.w.nodeCount)
        print "Library : " + str(self.w.libraryTypeName)
        print "Version : " + str(self.w.libraryVersion)
        print " "
        print "list of nodes :"
        ln = self.w.nodes
        for n in ln:
            lu = datetime.datetime.fromtimestamp(self.w.nodes[n].lastUpdate)
            print "node ", self.w.nodes[n].id, " type ", self.w.nodes[n].productType, " last update", lu.ctime()
            if self.w.nodes[n].productType != 'Static PC Controller':
                for val in self.w.nodes[n].values:
                    print "    ", self.w.nodes[n].values[val].valueData['label'], self.w.nodes[n].values[val].valueData['value'], self.w.nodes[n].values[val].valueData['units'] 
        print "fin du listage des nodes."

    def sendOn(self, node):
        print "node : " + node
        print "commande : On"
        self.node = int(node)
        self.w.setNodeOn(self.w.nodes[self.node])
    def sendOff(self, node):
        print "node : " + node
        print "commande : Off"
        self.node = int(node)
        self.w.setNodeOff(self.w.nodes[self.node])
    def sendLevel(self, node, lvl):
        print "node : " + node
        print "commande : level " + lvl
        self.node = int(node)
        self.lvl = int(lvl)
        self.w.setNodeLevel(self.w.nodes[self.node], self.lvl)
    def sendInfo(self, node):
        print "node : " + node
        print "commande : Info"
        self.node = int(node)
        self.w.refresh(self.w.nodes[self.node])
        nodeid = node
        type = self.w.nodes[self.node].productType
        if type.find('hermostat') >= 0:
            commande = "on,off,level,mode,fan-mode,setpoint,info"
        elif type.find('witch') >= 0:
           if type.find('ultilevel') >= 0:
               commande = "on,off,level,info"
           else:
               commande = "on,off,info"
        else:
           commande = "info"
        print "node = " + node + " type = " + type + " commande = " + commande
        resp = {}
        resp['node'] = node
        resp['type'] = type
        resp['commands'] = commande
        resp['modes'] = ' '
        resp['fan-modes'] = ' '
        resp['setpoints'] = ' '
        resp['states'] = ' '
        resp['fan-states'] = ' '
        print resp
        self._cb('xpl-stat', 'zwave.info', resp)

