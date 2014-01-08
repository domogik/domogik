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

import logging
import logging.handlers
from wsgiref.simple_server import make_server
from ws4py.server.wsgirefserver import WSGIServer, WebSocketWSGIRequestHandler
from ws4py.server.wsgiutils import WebSocketWSGIApplication
from ws4py.websocket import WebSocket
from ws4py import configure_logger as wsServer_logger
import threading
import json
import time
import os


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
        fName = "//var//log/domogik//wsuiserver.log"
        self.log = log
        if self.log :
            for h in log.__dict__['handlers']:
                if h.__class__.__name__ in ['FileHandler', 'TimedRotatingFileHandler','RotatingFileHandler', 'WatchedFileHandler']:
                    fName = os.path.dirname(h.baseFilename) + "/wsuiserver.log"
                    break
            logLevel = self.log.getEffectiveLevel()
        else : logLevel = logging.DEBUG
        self._wsLogws = wsServer_logger(level = logLevel)
        logfmt = logging.Formatter("[%(asctime)s] %(levelname)s %(message)s")
        handler = logging.handlers.RotatingFileHandler(fName, maxBytes=10485760, backupCount=5)
        handler.setLevel(logging.DEBUG)
        handler.setFormatter(logfmt)
        self._wsLogws.addHandler(handler)
        self.logMsg("info", "Log WS Server level {0} on : {1}".format(logLevel , fName))

        global __ctrlServer__
        # check free port
        for s in __ctrlServer__ :
            if s.port == port :
                self.logMsg("error", "Creating WS server error, port %d allready used."  % port)
                raise WsUIServerException ("Creating WS server error, port %d allready used."  % port)
        self.logMsg("debug", "Initializing WebSocket server plugin.....")
        self.buffer = []
        self.clients = set()
        self.fail_clients = set()
        self.running = False
        self.port = port
        self.cb_recept = cb_recept
        self.server = None
        self.server = make_server('', port, server_class=WSGIServer,
                     handler_class=WebSocketWSGIRequestHandler,
                     app=WebSocketWSGIApplication(handler_cls=WebSocketsHandler))
        if not self.server : raise WsUIServerException('Error websocket server creation, check if there is any other running plugin instance.')
        self.server.initialize_websockets_manager()
        __ctrlServer__.append(self)
        servUI = threading.Thread(None, self.run, "th_WSserv_msg_to_ui", (), {} )
        servUI.start()
        time.sleep(0.1)
        self.logMsg("info", "WebSocket server started on port : %d" %self.port)
        print "**************** WebSocket server is started on port %d ********************" %self.port
        
    def run(self):
        """Starting server in forever mode , calling by thread start.""" 
        # TODO : Ajouter la gestion d'une exception en cas d'erreur sur le server
        print "**************** Starting WebSocket server forever **************"
        self.logMsg("info", "Starting WebSocket server forever on port : %d" %self.port)
        self.running = True
        self.server.serve_forever()
    
    def close(self):
        """Closing server"""
        self.server.server_close()
        self.logMsg("info",  "WebSocket server forever on port : %d closed" %self.port)
        
    def __del__(self):
        """Close server and Destroy class."""
        print ('server stopped')
        self.running = False
        if  self.server : self.server.server_close()
        if __ctrlServer__ : __ctrlServer__.remove(self)
        self.logMsg("info",  "WebSocket server forever on port : %d Destroyed" %self.port)

    def broadcastMessage(self, msg):
        """broadcast Message to all clients"""
        message = msg.copy()  # copy dict to ensure a memory change during process
        header = {'type':'pub',  'idws' : 'for each' , 'ip' : '0.0.0.0',  'timestamp' : long(time.time()*100)}
        message['header'] = header
        # It's a copy of ws4py part lib (ws4py/manager.py  def broadcast(self, message, binary=False):) to add individual header infos. For python 3 
        # TODO : For python 3 compatibility check code : ws_iter = websockets.itervalues() must be ws_iter = iter(websockets.values())
        with self.server.manager.lock: # to prevent some change in websocket list client
            websockets = self.server.manager.websockets.copy()
            ws_iter = websockets.itervalues()
        for ws in ws_iter:
            if not ws.terminated:                
                try:
                    message['header']  = {'type':'pub', 'idws' : ws.peer_address[1] , 'ip' : ws.peer_address[0],  'timestamp' : long(time.time()*100)}
                    ws.send(json.dumps(message))
                    print "Server broadcasting sended to : ",  message['header']['idws']
                    print message
              #      self.logMsg("debug", "Server broadcasting sended to : {0}".format(message['header']['idws']))
                except Exception:
                    self.logMsg("debug",  "Failed sockets : {0}:{1}".format(ws.peer_address[0], ws.peer_address[1]))
                    pass

    def sendAck(self, ackMessage):
        """Send a confirmation message  'Ack'  to client"""
        ackMsg = ackMessage.copy()  # copy dict to ensure a memory change during process
        if ackMsg['header'] :
            # TODO : For python 3 compatibility check code : ws_iter = websockets.itervalues() must be ws_iter = iter(websockets.values())
            with self.server.manager.lock: # to prevent some change in websocket list client
                websockets = self.server.manager.websockets.copy()
                ws_iter = websockets.itervalues()
            for ws in ws_iter :
                if not ws.terminated:                
                    if ws.peer_address[1] == ackMsg['header']['idws'] :
                        try :
                            ws.send(json.dumps(ackMsg))
                            info = {}
                            for k in ackMsg :
                                if k != "data" and k != "header":  info[k] = ackMsg[k]
                            self.logMsg("debug", "Ack sended to WebSocket client : {0}:{1} => {2}".format(ackMsg['header']['ip'], ackMsg['header']['idws'],  info))
                        except Exception:
                            self.logMsg("debug",  "Failed sockets : {0}:{1}".format(ws.peer_address[0], ws.peer_address[1]))
                            pass

    def logMsg(self, type = "info", msg =""):
        """Log msg in plugin and wsuiserver"""
        if msg !="":
            if type =='info' : 
                if self.log : self.log.info(msg)
                self._wsLogws.info(msg)
            elif type == 'debug' :
                if self.log : self.log.debug(msg)
                self._wsLogws.debug(msg)
            elif type == 'error' :
                if self.log : self.log.error(msg)
                self._wsLogws.error(msg)
            elif type == 'warning' :
                if self.log : self.log.warning(msg)
                self._wsLogws.warning(msg)
            elif type == 'critical' :
                if self.log : self.log.critical(msg)
                self._wsLogws.critical(msg)
           
            
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
        self.server.logMsg("info",  "A new WebSocket client connected : %s:%s"  % (self.peer_address[0], self.peer_address[1]))
        self.send(json.dumps({'header': {'type' : 'confirm-connect', 'id' : 'ws_serverUI',  'idws': self.peer_address[1]}}))
        print 'WebSockect Message confirmation send from open to client',  self.peer_address[1] 
        self.confirmed = False

    def closed(self, code,  status):
        """Call at client closing or lost"""
        print 'Client WebSocket supprimer',  code,  status,  self.connection
        self.server.logMsg("info",  "WebSocket client disconnected : %s" % self.connection )

        
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
            self.server.logMsg("debug",  "WebSocket client error parsing msg : %s , Message : %s" % (e, str(message)))
        else :
      #      self.server.logMsg("debug",  "client received msg : {0}".format(header))
            if header['type']  == 'ack-connect':
                self.confirmed = True
                self.send(json.dumps({'header': {'type' : 'confirm-connect', 'id' : 'ws_serverUI',  'idws': self.peer_address[1]}}))
                self.server.logMsg("debug", 'WebSockect client connection confirmed by received, send client identity : {0}'.format(self.peer_address[1]))
            elif header['type']  == 'server-hbeat':
                self.sendAck(msg)
            elif self.confirmed == True :
                print '   Send to callback'
                if self.server.cb_recept : self.server.cb_recept(msg)
            if header['type'] == "ack" : self.sendAck({'msg':msg})
        print '++++++++++  End Websocket reception  +++++++++++'
        
    def sendAck(self, msg):
        """Send return confirmation message (Ack)."""
        msg.update({'header': {'type':'ack', 'idws' : self.peer_address[1] , 'ip' : self.peer_address[0],  'timestamp' : long(time.time()*100)}})
        self.send(json.dumps(msg))
        self.server.logMsg("debug",  "WebSocket Client have send Ack : {0}".format(msg))

def getServerOnPort(port):
    server = None
    for s in __ctrlServer__ :  # Find conresponding server object
        if s.port == port : 
            server = s
            break
    return server
