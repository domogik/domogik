#!/usr/bin/env python
# -*- coding: utf-8 -*-

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
        pyozw_dir = str(pyozw_path)
        pyozw_conf = str(pyozw_path) + "/openzwave/config/"
        sys.path.insert(0,pyozw_dir)
	import openzwave
	from openzwave import PyManager
	options = openzwave.PyOptions()
	options.create(pyozw_conf,"","")
	options.lock()
	manager = openzwave.PyManager()
	manager.create()
	
	# callback order: (notificationtype, homeid, nodeid, ValueID, groupidx, event)
	def callback2(args):
	    allowtype=['Battery Level','Relative Humidity','Temperature','Sensor']
	    resp = {}
	    if args:
		MyHomeId = args['homeId']
		resp['device'] = args['nodeId']
	        v = args['valueId']
		if v.has_key('label'): resp['type'] = v['label']
	        if v.has_key('value'): resp['current'] = v['value']
		if v.has_key('units') and (len(v['units']) > 0): resp['units'] = v['units']
		if v['label'] in allowtype:
		    print('\n-----------------------\nEnvoi du Message XPL:\n')
		    print resp
		    print('\n-----------------------\n')
		    self._cb('xpl-stat', 'sensor.basic', resp)

        manager.addWatcher(callback2)
        manager.addDriver(serial_port)

	
	# crappy loop to keep this thread
	try:
	    while 1:
	        pass
	except KeyboardInterrupt:
	    pass


    def sendOn(self, node):
	#print "HomeId : " + MyHomeId
        print "node : " + node
        print "commande : On"
        self.node = int(node)
	#manager.setNodeOn(self, MyHomeId, node)

