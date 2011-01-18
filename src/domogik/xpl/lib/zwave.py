#!/usr/bin/python
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

@author: Mika64 <ricart.michael@gmail.com>
@copyright: (C) 2007-2009 Domogik project
@license: GPL(v3)
@organization: Domogik
"""


import binascii
import threading
import serial
from time import sleep

class ZwaveException(Exception):
    '''
    Zwave Exception
    '''
            
    def __init__(self, value):
        Exception.__init__(self)
        self.value = value
                                
    def __str__(self):
        return repr(self.value)
                                            

class ZWave(threading.Thread):
    """
    ZWave class test
    """

    def __init__(self, serial_port_no, speed, read,log):
        """initialisation serial port
        """
        self.log = log
        self.read = read
        threading.Thread.__init__(self, target=self.run)
        self.__myser = serial.Serial(serial_port_no, speed, timeout=0.5)
        self._tosend = None
        self.listen = None
        self.ready = True
        ## Type Of Frame ##
        self.Type = {'20':'Home ID',
                '02':'Network Discovery',
                '41':'Info',
                '13':'level',
                '07':'API Version',
                '4a':'Association',
                '4b':'Delete',
                '49':'unknow'}
        self.sendType = dict([(self.Type[k], k) for k in self.Type])
	self.liste=[]

    def stop(self):
        """ Stop class
        """
        self.ready = False

    def run(self):
        """ Start Class ZWave
        """
        while True :        
            self.com()
            self.decode()
            ## ready to receive/send frame ##
            self.ready = True

    def send(self, command, nodeID = None, option = None):
        """ send fonction
            SOF = Start Of Frame
            level command : off = 00
                            on = other value if not dimmer
                            lvl = XX (% in hexa fore dimmer)
        """
        self.nodeID = nodeID
        if nodeID!= None:
            nodeID=binascii.hexlify(chr(int(nodeID)))
        SOF = '01'
        request = '00'
        sleep(0.3)
        if command == 'level':
            cmd = self.sendType[command]
            self.level = option
            option = binascii.hexlify(chr(int(option)*255/100))
            option = '032001'+option+'0503'
        elif command == 'on':
            cmd = '13'
            self.level = '100'
            option = '032001FF0503'
        elif command == 'off':
            cmd = '13'
            self.level = '0'
            option = '032001000503'
        elif command == 'Association':
            cmd = self.sendType[command]
            option = '01'
        else:
            cmd = self.sendType[command]
        if option == None:
            option = ''
        if nodeID == None:
            nodeID = ''            
        ## Basic frame without len,SOF and checksum ##
        frametosend = request + cmd + nodeID + option
        ## Calcul of length ##
        length = binascii.hexlify(chr(((len(frametosend))/2)+1))
        ## Frame without checksum ##
        frametosend = SOF + length + frametosend
        ## calcul and add checksum ##
        self.__checksum(frametosend)
        frametosend = frametosend + self.chk
        self._tosend = frametosend

    def com(self):
        """ Communication fonction with serial port
            SOF = Start Of Frame
        """
        SOF = '01'
        frame = ''
        frame_length = 0
        frame_started = False
        while self.ready == True :
            ## send frame ##
            if self._tosend != None:
                self.__myser.write(self._tosend.decode('HEX'))
                self._tosend = None
            ## receive frame ##
            char = self.__myser.read(1)
            hexchar = binascii.hexlify(char)
            if char == '':
                pass
            elif hexchar == SOF and frame_started == False:
                frame_started = True
                frame = SOF
                frame_length = 1
            elif frame_started == True and frame_length == 1:
                #On vient de démarrer une trame mais pas encore eu la longueur
                frame_length = (int(hexchar, 16))*2 +4 # On converti la longueur en int
                frame += hexchar
            else:
                #On a démarré une trame et on a eu la longueur, on rempli donc
                frame += hexchar
                if len(frame) == frame_length:
                   # On est à la fin de la trame, on la print
                   # print "Nouvelle trame : %s" % frame
                   # Calcul et verification du checksum
                   chksum = frame[(frame_length-2):frame_length]
                   self.__checksum(frame[0:frame_length-2])
                   if chksum == self.chk:
                        ##ACK
                       self.__myser.write('06'.decode('HEX'))
                       self.listen = frame
                    #    print frame
                    # Et on réinitialise
                   frame_started = False
                   frame = ''
                   frame_length = 0
                   self.ready = False

    def decode (self):
        """ decode frame fonction
        """
        TOF = ''
        command = ''
        data = ''
        if self.listen != None:
            TOF = self.listen[6:8]
            command = self.Type[TOF]
            data = self.listen[8:((len(self.listen))-2)]
            self.listen = None
        if command == 'level':
            if len(data) == 4:
                if data[2:4] == '01':
                    nodeID = data[0:2]
                    self.read({'command' : command,
                                'node' : nodeID,
                                'info': 'unresponsive'})
                    self.level = ''
                elif data[2:4] == '00':
                    print "Status of node %s as change, its level is : %s" % (self.nodeID,self.level)
                    self.read({'event' : command,
                                'node' : self.nodeID,
                                'level': int(self.level)})
            elif command == 'level' and data == '01':
                print "Node ID correct"
        elif command == 'Home ID':
            home=data[0:8]
            print "Home ID = %s" % home
            mess={'command':command,
                       'Home ID':home}
            self.read(mess)
        elif command == 'Association':
            print data
        elif command == 'Info':
            if data == '000000030000':
                print "Unknow device %s" % self.nodeID            
            data=data[6:]
            print data
            basicclass={'01':'CONTROLLER',
                        '02':'STATIC CONTROLLER',
                        '03':'SLAVE',
                        '04':'ROUTING SLAVE'}
            TOD={'01':'CONTROLLER',
                '10':'SWITCH/APPLIANCE',
                '11':'DIMMER',
                '12':'TRANSMITTER',
                '08':'THERMOSTAT',
                '09':'SHUTTER',
                '20':'BASIC CLASS'}
            if data[0:2] == '02':
                self.read = 'STATIC CONTROLLER'
            else:
                self.read = ({'Info' : basicclass[data[0:2]] + ' , ' + TOD[data[2:4]]})
            
        elif command == 'Network Discovery':
            n=0
            list=[]
            data = data[6:]
            while n!=58:
                a=bin((int(data[n:n+2],16)))[2:]
                if data[n:n+2]!='00':
                    while len(a)!=8:
                        a='0'+a
                    i=7
                    m=1
                    while i!=-1:                        
                        if a[i]=='1':
                            m=m+(8*(n/2))
                            list.append(m)
                        m=m+1
                        i=i-1
                n=n+2
            if list!=[]:
                self.read({'Find':list[0:]})
        if command == 'unknow':
            print data
        TOF = ''
        command = ''
        data = ''

    def __checksum(self, frametochck):
        """ checksum calcul fonction
        XOR logical operation with all octet of frame without SOF and checksum
        """
        self.chk = None
        i = 2
        chk = 0
        while i != (len(frametochck)):
            chk = chk^(int(frametochck[i:(i+2)],16))
            i = i + 2
        chk = 255 - chk
        chk = binascii.hexlify(chr(chk))
        self.chk = chk
