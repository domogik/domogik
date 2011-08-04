#!/usr/bin/python
# -*- coding: latin-1 -*-

""" This file is part of B{Domogik} project (U{http://www.domogik.org}).

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

ZiBase support. www.zodianet.com

Implements
==========

- APIZiBase

@author: Cedric BOLLINI <cb.dev@sfr.fr>
@copyright: (C) 2007-2011 Domogik project
@license: GPL(v3)

This library based on ZiBase SDK 1.6 by bgarel and modify by Cedric BOLLINI

"""


from domogik.xpl.common.xplmessage import XplMessage
from array import array
import socket
import struct
import fcntl
import sys
import re
import threading
    
class ZbAction:
    """ ZiBase action """
    OFF = 0
    ON = 1
    DIM_BRIGHT = 2
    ALL_LIGHTS_ON = 4
    ALL_LIGHTS_OFF = 5
    ALL_OFF = 6
    ASSOC = 7    

class ZbRequest(object):
    
    def __init__(self):
        self.header = bytearray("ZSIG")
        self.command = 0
        self.reserved1 = ''
        self.zibaseId = ''
        self.reserved2 = ''        
        self.param1 = 0
        self.param2 = 0
        self.param3 = 0
        self.param4 = 0
        self.myCount = 0
        self.yourCount = 0        
        self.message = ''      
     
        
    def toBinaryArray(self):
        buffer = array('B')
        buffer = self.header
        buffer.extend(struct.pack('!H', self.command))
        buffer.extend(self.reserved1.rjust(16, chr(0)))
        buffer.extend(self.zibaseId.rjust(16, chr(0)))
        buffer.extend(self.reserved2.rjust(12, chr(0)))
        buffer.extend(struct.pack('!I', self.param1))
        buffer.extend(struct.pack('!I', self.param2))
        buffer.extend(struct.pack('!I', self.param3))
        buffer.extend(struct.pack('!I', self.param4))
        buffer.extend(struct.pack('!H', self.myCount))
        buffer.extend(struct.pack('!H', self.yourCount))
        if len(self.message) > 0:
            buffer.extend(self.message.ljust(96, chr(0)))
        return buffer
    

class ZbResponse(object):
    """ Response from ZiBase """
    
    def __init__(self, buffer):             
        self.header = buffer[0:4]
        self.command = struct.unpack("!H", buffer[4:6])[0]
        self.reserved1 = buffer[6:22]
        self.zibaseId = buffer[22:38]
        self.reserved2 = buffer[38:50]        
        self.param1 = struct.unpack("!I", buffer[50:54])[0]
        self.param2 = struct.unpack("!I", buffer[54:58])[0]
        self.param3 = struct.unpack("!I", buffer[58:62])[0]
        self.param4 = struct.unpack("!I", buffer[62:66])[0]
        self.myCount = struct.unpack("!H", buffer[66:68])[0]
        self.yourCount = struct.unpack("!H", buffer[68:70])[0]
        self.message = buffer[70:]    

    
class APIZiBase(object):
    """ Library to use ZiBase """
    
    def __init__(self, log, ip):
        """ Init API ZiBase """
	self._log = log
        self.ip = ip
        self.port = 49999
    
         
    def sendRequest(self, request):
        """ Send request to ZiBase """
        buffer = request.toBinaryArray()
        response = None
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(5)
        s.connect((self.ip, self.port))        
        s.send(buffer)
        ack = s.recv(512)
        if len(ack) > 0:
            response = ZbResponse(ack)        
        s.close()
        return response
    
    
    def sendCommand(self, address, action, protocol = 0, dimLevel = 0, nbBurst = 1):
        """ Send Command to ZiBase """
        if len(address) >= 2:            
            address = address.upper()
            req = ZbRequest()            
            req.command = 11         
            if action == ZbAction.DIM_BRIGHT and dimLevel == 0:
                action = ZbAction.OFF            
            req.param2 = action
            req.param2 |= (protocol & 0xFF) << 0x08
            if action == ZbAction.DIM_BRIGHT:
                req.param2 |= (dimLevel & 0xFF) << 0x10
            if nbBurst > 1:
                req.param2 |= (nbBurst & 0xFF) << 0x18                        
            req.param3 = int(address[1:]) - 1
            req.param4 = ord(address[0]) - 0x41                        
            self.sendRequest(req)

    def Connect(self,ip_host,port_host):
        req = ZbRequest()
        req.command = 13
        req.param1 =iptohex(ip_host)
        req.param2 = port_host
        req.param3 = 0
        req.param4 = 0
        self._log.debug('Send request for link')
        rep=self.sendRequest(req)

    def Disconnect(self,ip_host,port_host):
        req = ZbRequest()
        req.command = 22
        req.param1 =iptohex(ip_host)
        req.param2 = port_host
        req.param3 = 0
        req.param4 = 0
        self._log.debug('Send request for unlink')
        rep=self.sendRequest(req)

def get_ip_address(ifname):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    return socket.inet_ntoa(fcntl.ioctl(
        s.fileno(),
        0x8915,  # SIOCGIFADDR
        struct.pack('256s', ifname[:15])
    )[20:24])

def iptohex(ip):
    ip=ip.split('.')
    x=24
    y=0
    for z in ip:
        y|=(int(z) & 0xFF) << x
        x=x-8
    return y

class ServerZiBase(threading.Thread):
    def __init__(self,log,ip,port,hubxpl):
        threading.Thread.__init__(self)
        self.serv=socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.port=port
        self.ip=ip
        self.serv.bind(('',self.port))
        self.log=log
        self.log.info("Server Ready on port=%s" % (str(self.port)))
        self.buf=1024
        self.hxpl=hubxpl

    def run(self):

        self.log.info("Server Start on port=%s" % (str(self.port)))
        self._listen=True
        # Server are listenning
        while self._listen:
            
            self.req, self.adr = self.serv.recvfrom(self.buf)

            if self.req=='FIN':
                self.log.debug("Stop Server on port=%s in progress" % (self.port))
                self._listen=False
                break

            try:
                if '<ch/>' in self.req:
                    self.req=self.req.replace('<ch/>','</ch>')

                self.data=re.findall(r'<(.*?)>(.*?)</.*?>', self.req)
            except:
                self.log.error("%s" % sys.exc_info()[1])

            if "Received radio ID" in self.req:
                self.log.debug("Received datas ZiBase")
                self.log.debug(self.req)
                datas=[]
                for elmt in self.data:
                    if elmt[0]=='id':
                        self.id=elmt[1]
                    else:
                        datas+=[elmt[0] + ':' + elmt[1]]

                self.send_xpl(datas)


            if "linked to host" in self.req:
                for elmt in self.data:
                    if elmt[0]=='zip':
                        zip=elmt[1]
                    if elmt[0]=='zudp':
                        zudp=elmt[1]
                self.log.info("ZiBase linked to DMG IP=%s on port=%s" % (zip,zudp))
                    
        self.serv.close()

    def stop(self):
        self.serv.sendto('FIN',(self.ip,self.port))
        while self._listen:
            print "Wait stop"
        self.log.debug("Server stopped on port=%s" % (self.port))

    def send_xpl(self, datas):
        """ Send xpl-trig to give status change
        """
        type={
            'tem' : 'temp',
            'hum' : 'humidity',
            'bat' : 'battery',
            'kwh' : 'energy',
            'kw' : 'power',
            'tra' : 'raintotal',
            'cra' : 'rainrate',
            'uvl' : 'uv',
            'awi' : 'speed',
            'dir' : 'direction',
            'temc' : 'setpoint',
            'sta' : 'status'
            }

        for data in datas:
            elmt=data.split(':')
            if elmt[0] in type.keys():
                msg = XplMessage()
                msg.set_type("xpl-trig")
                msg.set_schema('sensor.basic')
                msg.add_data({'device' :  self.id})
                msg.add_data({'type' :  type[elmt[0]]})
                msg.add_data({'current' :  elmt[1]})
                self.hxpl.send(msg)




        
      
      
