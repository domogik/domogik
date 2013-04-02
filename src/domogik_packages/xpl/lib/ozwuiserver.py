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
@copyright: (C) 2007-2013 Domogik projectiport
@license: GPL(v3)
@organization: Domogik
"""

from wsgiref.simple_server import make_server
from ws4py.server.wsgirefserver import WSGIServer, WebSocketWSGIRequestHandler
from ws4py.server.wsgiutils import WebSocketWSGIApplication
from ws4py.websocket import WebSocket
import threading
import json
import time

__ctrlServer__ = None  # juste one server for websockets recover

ReqD = {'toto':'moi', 'data': {'v1':1,  'v2': 'titi', 'v3': True},  'fin': 'et voila / % - \\"44" & ! §'}
RespD = {'Value': 454545L, 'long' :'Insensitiveness to temperature changes. This is the maximum acceptable difference between the last ' +
               'reported temperature and the current temperature taken from the sensor. '+
               'If the temperatures differ by the set value or more, then a report with the current temperature value is sent ' +
               'to the device assigned to association group no. 3. Intervals between taking readings from sensors are specified ' +
               'by parameter no. 10.' +
			  'Possible parameter settings:0 – 255 [0oC to 16oC] [0 oF – 28.8oF] \n' +
			  'In order to set the appropriate value of the parameter, the following formula should be used: \n' +
			  'x = delta T x 16 - for Celsius \n' +
			  'x = delta T x 80 / 9 - for Fahrenheit \n' +
			  'x – parameter value \n' +
			  'delta T – maximum acceptable temperature gradient in Celsius or Fahrenheit \n' +
			  'If the value is set to 0, then information about the temperature will be sent every time, immediately once the readings have been taken from the sensor', 
              'tab': ['aa', 'zzz', 'rere', 'fff'], 
              'extra': ' Which reports need to send in group3. Format is as follows:\n' +
                'Byte 1 (msb): Reserved\n' +
                'Byte 2: Reserved\n' +
                'Byte 3: Bit 7: reserved\n' +
                'Bit 6: reserved\n' +
                'Bit 5: Auto Send Meter Report (for kWh) at the group time interval (Clamp 3)\n' +
                'Bit 4: Auto Send Meter Report (for kWh) at the group time interval (Clamp 2)\n' +
                'Bit 3: Auto Send Meter Report (for kWh) at the group time interval (Clamp 1)\n' +
                'Bit 2: Auto Send Meter Report (for watts) at the group time interval (Clamp 3)\n' +
                'Bit 1: Auto Send Meter Report (for watts) at the group time interval (Clamp 2)\n' +
                'Bit 0: Auto Send Meter Report (for watts) at the group time interval (Clamp 1)\n' +
                'Byte 4 (lsb): Bit 7: reserved\n' +
                'Bit 6: reserved\n' +
                'Bit 5: reserved\n' +
                'Bit 4: reserved\n' +
                'Bit 3: Auto Send Meter Report (for kWh) at the group time interval (whole HEM)\n' +
                'Bit 2: Auto Send Meter Report (for watts) at the group time interval (whole HEM)\n' +
                'Bit 1: Auto Send Multilevel Sensor Report (for watts) at the group time interval (whole HEM)\n' +
                'Bit 0: Auto Send Battery Report at the group time interval (whole HEM)'}

class BroadcastServer(object):
    def __init__(self,  port=5570,  cb_recept = None,  log = None ):
        global __ctrlServer__
        self.buffer = []
        self.clients = set()
        self.fail_clients = set()
        self.running = False
        self.port = port
        self.cb_recept = cb_recept
        self.log = log
        self.server = make_server('', port, server_class=WSGIServer,
                     handler_class=WebSocketWSGIRequestHandler,
                     app=WebSocketWSGIApplication(handler_cls=WebSocketsHandler))
        self.server.initialize_websockets_manager()
        __ctrlServer__ = self
        servUI = threading.Thread(None, self.run, "th_WSserv_msg_to_ui", (), {} )
        servUI.start()
        time.sleep(0.1)
        self.log.info('WebSocket server started on port : %d' %self.port)
        print "**************** WebSocket server is started ********************"
        
    def run(self):
        # TODO : Ajouter la gestion d'un exception en cas d'erreur sur le server
        print "**************** Starting WebSocket server forever **************"
        self.log.info('Starting WebSocket server forever')
        self.running = True
        self.server.serve_forever()
    
    def close(self):
        self.server.server_close()
        
    def __del__(self):
        print ('server stopped')
        self.running = False
        self.server.stop()
        
    def broadcastMessage(self, message):
        header = {'type':'pub',  'idws' : 'for each' , 'ip' : '0.0.0.0',  'timestamp' : long(time.time()*100)}
        message['header'] = header
        info = 'Websocket server sending for %d client(s) : %s' %(len(self.server.manager.websockets),  str(message))
     #   print info
        self.log.debug(info)
        for ws in self.server.manager.websockets.itervalues():
            try:
                message['header']  = {'type':'pub', 'idws' : ws.peer_address[1] , 'ip' : ws.peer_address[0],  'timestamp' : long(time.time()*100)}
                ws.send(json.dumps(message))
                print "Send to : ",  message['header']['idws']
                print message
            except Exception:
                self.server.manager.remove(ws)
                print "Failed sockets"
                continue
                
    def sendAck(self, ackMsg):
        if ackMsg['header'] :
            for ws in self.server.manager.websockets.itervalues():
                if ws.peer_address[1] == ackMsg['header']['idws'] :
                    print 'Send Ack on WebSocket'
                    ws.send(json.dumps(ackMsg))

class WebSocketsHandler(WebSocket):
    def opened(self):
        global __ctrlServer__
        print 'Nouveau client WebSocket',  self.peer_address
        __ctrlServer__ .log.info('A new WebSocket client connected : %s : %s'  % (self.peer_address[0], self.peer_address[1]))
        self.send(json.dumps({'header': {'type' : 'confirm-connect', 'id' : 'ozwave_serverUI',  'idws': self.peer_address[1]}}))
        self.confirmed = False

        
    def closed(self, code,  status):
        global __ctrlServer__
        print 'Client WebSocket supprimer',  code,  status,  self.connection
        __ctrlServer__ .log.info('WebSocket client disconnected : %s' % self.connection )

        
    def received_message(self, message):
        global __ctrlServer__
        t = time.time()              # Getting date/time
        print 'message recu : ',  message
        session = self.environ.get('REMOTE_ADDR')
        annonce = '%s connected' % session
        print 'Recept websocket message, session on : ',  session,  ' client : ',  self.peer_address[1]
        try :
            msg = json.loads(str(message))
     #       print 'parse ok'
            header = msg['header'] 
        except TypeError as e :
            print 'Error parsing websocket msg :',  e
            __ctrlServer__ .log.debug('WebSocket client error parsing msg : %s , Message : %s' %(e, str(message)))
        else :
            if header['type']  == 'ack-connect':
                self.confirmed = True 
                print ('WebSockect connection confirmed')
            elif msg['request']  == 'server-hbeat':
                self.sendAck(msg)
            elif self.confirmed == True :
                __ctrlServer__.cb_recept(msg)
                print 'Send to callback'
            if header['type'] == "ack" : self.sendAck({'msg':msg})
            if msg =='quit' : running =False
        print '++++++++++++++++++++++++++  fin Websocket reception'
        
        
    def sendAck(self, msg):
        global __ctrlServer__
        print 'WebSocket send Ack'
        msg.update({'header': {'type':'ack', 'idws' : self.peer_address[1] , 'ip' : self.peer_address[0],  'timestamp' : long(time.time()*100)}})
        self.send(json.dumps(msg))
