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

Code Purpose
==============

Template for using WebSocket server for plugins

Implements
==========

Get exemple to include and manage a WebServer in your plugin.
This server provides features dialog between a plugin and UI using websocket HTML5 functionnality

All message have an header JSON with keys :
    - 'type': give the type of message, values can  be:
        -'req' : a simple client resquest, this type is passed to callback.
        -'req-ack' : a client resquest with confirmation requested , this type is passed to callback.
        -'pub' : Automaticly select with server.broadcastMessage function.
                Next two keys help to secure and validate the client connection.
        -'confirm-connect' : Internal server type for confirm to client connection accepted. See UI client part.
                                    This message type is send automaticly to client when he ask for connection. Add 2 keys for identity : 
                                -'id' : 'ws_serverUI' : constante string
                                -'idws' : peer_adresss, id that the client keeps for identification.
        -'ack-connect' : Internal server type to confirm that client have recept first confirmation ('confirm-connect').
                              The client must send this message type to finalized connection. See UI client part.
                              
        -'server-hbeat' : Internal server type for client check server running.
                               server send automaticly an confirmation message. See UI client part if you implement it.
                               
    - 'idws' : Identify resquesting client. See UI client part.
    - 'idmsg: Identify of individual resquet. See UI client part.
    - 'ip' : Identify resquesting IP client. 
    - 'timestamp' : A reference time when message was sent. See UI client part.

@author: Nico <nico84dev@gmail.com>
@copyright: (C) 2007-2013 Domogik projectiport
@license: GPL(v3)
@organization: Domogik
"""

# in files  src/domogik_packages/xpl/lib/fooplugin.py

from wsuiserver import BroadcastServer  # just Broadcasting Server needed
import time
import threading

# JSON data for testing msg
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

class YourFooPlugin(threading.Thread): 
    """
    Your classic declaration domogik plugin class.
    """

    def __init__(self,  port):
        """
        Your init sequence and add webserver declaration.
        """
        #Your specific code.........
        #Add lines :
        self._wsPort = port
        self._log = None
        self.serverUI =  BroadcastServer(self._wsPort,  self.cb_ServerWS,  self._log) # Starting Websocket server
        #           @ param  self._wsPort :  Port network, which must be opened for external access. 
        #                                               You could get it by plugin configuration : self._wsPort = int(self._configPlug.query('fooplugin', 'wsportserver'))
        #                                               Port number must be unique for all WsServer instances in all domogik plugins. If port already exist an exception is raised.
        #                                               So it is the user to be careful.
        #           @ param self.cb_ServerWS : Callback function that must manage messages, see below. If not present or None server don't dispatch messages to plugin
        #           @ param self._log : It can be log instance like self.log object of XplPlugin class or other log déclaration
        #                                       if present or not None server log some infos, debug and error in this instance.
        #......Your specific code.........
        
    def cb_ServerWS(self, message):
        """
        Callback to handle messages from server Websocket, principaly UI.
        Messages type resquest with or without Ack required.
        This an example you can develop it as you want !.
        You have just tu respect header ack message, see end function.
        """
        blockAck = False                                                                # Using if it necessary to block Ack message for any reason.
        report = {'error':  'message not handle'}                        # Reporting structure for data to report in message, It's better having an error key to handle it in UI.
        ackMsg = {}                                                                    #  Ack structure, for particulars params
        print "Handle a Requesting Call Back from UI" ,  message   # debug code
        if message['header']['type'] in ('req', 'req-ack'):            # check if a message type is a request.
            if message['request'] == 'foorequest1' :                      # here manage your own functions.
                report = self.foofunction1(message['fooparam'])           # Call your function, possibly with the parameters retrieved from the message.
                                                                                               # Attribute resulte in report structure JSON with error key empty if no error.
                                                                                               # example : {'error':"", 'fookey': "that you want", ...... }
                if not report['footest'] : blockAck = True    # Possibly add blocking ack for example.

            elif message['request'] == 'foorequest2' :
                report = self.foofunction2()
                ackMsg['fooparam'] = message['yourparticularparam']                       # If you need to recover a particular parameter in ack message you can assigned here.
                
            elif message['request'] == 'foorequest3' :
                if message.has_key('fooparam2'):                                                                  # put all tests you want.
                    report = self.foofunction3(message['fooparam1'],  message['fooparam2'])
                else : report = {'error':  'Invalide foo param2 format.'}                 # handle error key in local callback.

            else :
                report['error'] ='unknown request'                           # handle unknown request case.
                print "unknown request" # debug code

        if message['header']['type'] == 'req-ack' and not blockAck :   # check and prepare ack message 
            ackMsg['header'] = {'type': 'ack',  'idws' : message['header']['idws'], 'idmsg' : message['header']['idmsg'],
                                           'ip' : message['header']['ip'] , 'timestamp' : long(time.time()*100)}
                                           
            #           header composition keys :
            #                   - 'type': here must be 'ack'.
            #                   - 'idws' : recover orignal header key (message['header']['idws']), it's identify resquesting client.
            #                   - 'idmsg: recover orignal header key (message['header']['idmsg']), it's identify the individual resquet.
            #                   - 'ip' : recover orignal header key (message['header']['ip']), it's identify resquesting IP client.
            #                   - 'timestamp' : must be updated to give a reference time.
            
            ackMsg['request'] = message['request']
            if 'error' in report :                                                      # put error in ack structure if necessary
                ackMsg['error'] = report['error']
            else :
                ackMsg['error'] = ''
            ackMsg['data'] = report                                                 # put values reportin data key
            
            self.serverUI.sendAck(ackMsg)                                          # call server send function with parameters Ack structure 

    def stop(self):
        """
        Standard domogik stop function.
        """
         # Your specific code ....
        self.serverUI.close() # just call server closing
        
    def foofunction1(self,  param):
        return {'error': "", 'footest': True}

    def foofunction2(self):
        retval = {'error': ""}
        retval.update(RespD)
        return retval

    def foofunction3(self,  param1,  param2):
        return {'error': "Example error generated"}
    
    def anyFunction(self):
        """
        Example to implement a publishing message
        """
        # Your specific code ....
        # call broadcastMessage function with your JSON data as you want :)
        # server will dispatch 'pub' message to all client with good header :)
        self.serverUI.broadcastMessage({'fookey1': 'foovalue', 'fookeyx': {'anotherdic':'values'}, 'footab' : [1, 5, 10]})
        # .... Your specific code ....


# Not necessary code, just for example and main.
from ws4py.client import WebSocketBaseClient
from ws4py import format_addresses
from wsuiserver import getServerOnPort
import json
import random

class EchoClient(WebSocketBaseClient):
    """
    Python client example not necessary for UI
    """
    def handshake_ok(self):
        print " EchoClient Opening %s" % format_addresses(self)
        self.send(json.dumps({'header':{'type': 'ack-connect', 'idws':'request'}}))
        getServerOnPort(self.peer_address[1]).server.manager.add(self)

    def received_message(self, message):
        print "         Recept by EchoClient : " ,  message
        msg = json.loads(str(message))
        if msg['header']['type'] == "confirm-connect" : 
            ackmsg = dict(msg)
            ackmsg['header']['type'] = 'ack-connect'
            self.idws = ackmsg['header']['idws']
            self.ip = self.local_address[0]
            
    def sendRequest(self, request,  data):
        msg = {'header': {'type' : 'req-ack', 'idws': self.idws,  'ip': self.local_address[0], 
                                    'timestamp': long(time.time()*100), 'idmsg' : int((random.random() * 1000000) +1)}}
        msg['request'] = request
        msg.update(data)
        print 'Request EchoClient send' , msg
        self.send(json.dumps(msg))

if __name__ == '__main__':
    """
    Simple Example to run client and server
    """
    myPlugin1 = YourFooPlugin(5555)
    m1 = myPlugin1.serverUI.server.manager
    myPlugin2 = YourFooPlugin(5556)
    m2 = myPlugin2.serverUI.server.manager
    try:
        client2 = EchoClient('ws://localhost:%d/ws' % myPlugin2._wsPort)
        client2.connect()
        for i in range(2):
            client = EchoClient('ws://localhost:%d/ws' % myPlugin1._wsPort)
            client.connect()
        while True:
            for ws in m1.websockets.itervalues():
                if not ws.terminated:
                   break
            else:
                break
            time.sleep(5)
            message = ReqD
            message['from'] = 'Publish'
            myPlugin1.serverUI.broadcastMessage(message)
            time.sleep(2)
            client.sendRequest('foorequest1',  {'fooparam': 'foofoo', 'footest' : True})
            client.sendRequest('foorequest2',  {'yourparticularparam': 'foofoo'})
            client2.sendRequest('foorequest3',  {'fooparam1': 'foofoo',  'fooparam1': 56566.6, 'fooparam2': 56999})
            client.sendRequest('foorequest3',  {'fooparam1': 'foofoo',  'fooparam1': 56566.6})
            
    except KeyboardInterrupt:
        m1.close_all()
        myPlugin1.serverUI.close()
        m2.close_all()
        myPlugin2.serverUI.close()
