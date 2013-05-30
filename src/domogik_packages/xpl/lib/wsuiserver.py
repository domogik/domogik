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

WebSocket server for plugins

Implements
==========

Manage a server for dialog between a plugin and UI using websocket HTML5 functionnality

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

from wsgiref.simple_server import make_server
from ws4py.server.wsgirefserver import WSGIServer, WebSocketWSGIRequestHandler
from ws4py.server.wsgiutils import WebSocketWSGIApplication
from ws4py.websocket import WebSocket
import threading
import json
import time

__ctrlServer__ = []  # tab servers for websockets recover

class WsUIServerException(Exception):
    """"Websocket server generic exception class.
    """
    def __init__(self, value):
        """Initialisation"""
        Exception.__init__(self)
        self.msg = "Websocket server generic exception:"
        self.value = value
                                
    def __str__(self):
        """String format objet"""
        return repr(self.msg + ' ' + self.value)
        
class BroadcastServer(object):
    """Class de gestion du server websocket pour dialogue plugin UI"""
    def __init__(self,  port=5570,  cb_recept = None,  log = None ):
        global __ctrlServer__
        # check free port
        for s in __ctrlServer__ :
            if s.port == port :
                if log : log.error("Creating WS server error, port %d allready used."  % port)
                raise WsUIServerException ("Creating WS server error, port %d allready used."  % port)
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
        __ctrlServer__.append(self)
        servUI = threading.Thread(None, self.run, "th_WSserv_msg_to_ui", (), {} )
        servUI.start()
        time.sleep(0.1)
        if self.log : self.log.info('WebSocket server started on port : %d' %self.port)
        print "**************** WebSocket server is started on port %d ********************" %self.port
        
    def run(self):
        """Starting server in forever mode , calling by thread start.""" 
        # TODO : Ajouter la gestion d'une exception en cas d'erreur sur le server
        print "**************** Starting WebSocket server forever **************"
        if self.log : self.log.info('Starting WebSocket server forever on port : %d' %self.port)
        self.running = True
        self.server.serve_forever()
    
    def close(self):
        """Closing server"""
        self.server.server_close()
        if self.log : self.log.info('WebSocket server forever on port : %d closed' %self.port)
        
    def __del__(self):
        """Close server and Destroy class."""
        print ('server stopped')
        self.running = False
        self.server.server_close()
        __ctrlServer__.remove(self)
        if self.log : self.log.info('WebSocket server forever on port : %d Destroyed' %self.port)
        
    def broadcastMessage(self, message):
        """broadcast Message to all clients"""
        header = {'type':'pub',  'idws' : 'for each' , 'ip' : '0.0.0.0',  'timestamp' : long(time.time()*100)}
        message['header'] = header
        info = 'Websocket server sending for %d client(s) : %s' % (len(self.server.manager.websockets),  str(message))
     #   print info
        if self.log : self.log.debug(info)
        for ws in self.server.manager.websockets.itervalues():
            try:
                message['header']  = {'type':'pub', 'idws' : ws.peer_address[1] , 'ip' : ws.peer_address[0],  'timestamp' : long(time.time()*100)}
                print "Server broadcasting send to : ",  message['header']['idws']
                print message
                ws.send(json.dumps(message))
            except Exception:
                self.server.manager.remove(ws)
                print "Failed sockets"
                continue
                
    def sendAck(self, ackMsg):
        """Send a confirmation message  'Ack'  to client"""
        if ackMsg['header'] :
            for ws in self.server.manager.websockets.itervalues():
                if ws.peer_address[1] == ackMsg['header']['idws'] :
                    print 'Send Ack on WebSocket client',  ackMsg['header']['idws'] 
                    ws.send(json.dumps(ackMsg))

class WebSocketsHandler(WebSocket):
    """One Client Class par client, create by server, inherited from WebSocket class ."""
    def opened(self):
        """Call at client openning."""
        global __ctrlServer__
        port = self.sock.getsockname()[1]
        self.server = None
        for s in __ctrlServer__ :  # Find conresponding server object
            if s.port == port : self.server = s
        if not self.server :
            raise WsUIServerException ("Openning WS client error, port %d not find in server list."  % port)
        print 'New WebSocket client detected ',  self.peer_address
        if self.server.log : self.server.log.info('A new WebSocket client connected : %s : %s'  % (self.peer_address[0], self.peer_address[1]))
#        self.send(json.dumps({'header': {'type' : 'confirm-connect', 'id' : 'ws_serverUI',  'idws': self.peer_address[1]}}))
#        print 'Message confirmation send'
        self.confirmed = False

    def closed(self, code,  status):
        """Call at client closing or lost"""
        print 'Client WebSocket supprimer',  code,  status,  self.connection
        if self.server.log : self.server.log.info('WebSocket client disconnected : %s' % self.connection )

        
    def received_message(self, message):
        """Callback from recept client message, handle return confirmation message (Ack)."""
        print '  Recept from client, transfer to handler: ',  message
#        session = self.environ.get('REMOTE_ADDR')
#        print '    Recept websocket message, session on : ',  session,  ' client : ',  self.peer_address[1]
        try :
            msg = json.loads(str(message))
            header = msg['header'] 
        except TypeError as e :
            print '   Error parsing websocket msg :',  e
            if self.server.log : self.server.log.debug('WebSocket client error parsing msg : %s , Message : %s' % (e, str(message)))
        else :
            if header['type']  == 'ack-connect':
                self.confirmed = True
                self.send(json.dumps({'header': {'type' : 'confirm-connect', 'id' : 'ws_serverUI',  'idws': self.peer_address[1]}}))
                print '    WebSockect client connection confirmed, send client identity : ',  self.peer_address[1] 
            elif header['type']  == 'server-hbeat':
                self.sendAck(msg)
            elif self.confirmed == True :
                print '   Send to callback'
                if self.server.cb_recept : self.server.cb_recept(msg)
            if header['type'] == "ack" : self.sendAck({'msg':msg})
        print '++++++++++  End Websocket reception  +++++++++++'
        
    def sendAck(self, msg):
        """Send return confirmation message (Ack)."""
        print 'WebSocket send Ack'
        msg.update({'header': {'type':'ack', 'idws' : self.peer_address[1] , 'ip' : self.peer_address[0],  'timestamp' : long(time.time()*100)}})
        self.send(json.dumps(msg))

def getServerOnPort(port):
    server = None
    for s in __ctrlServer__ :  # Find conresponding server object
        if s.port == port : 
            server = s
            break
    return server
