#!/usr/bin/env python
# -*- encoding:utf-8 -*-

# Copyright 2009 Domogik project

# This file is part of Domogik.
# Domogik is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# Domogik is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with Domogik.  If not, see <http://www.gnu.org/licenses/>.

# Author: Yoann HINARD <yoann.hinard@gmail.com>

# $LastChangedBy:$
# $LastChangedDate:$
# $LastChangedRevision:$

#classe serial handler
#sert à envoyer les trames PLCbus présentes dans la queue d'émission sur le port série (gère la retransmission
#met les trames reçues dans une queue de reception (pour les envoyer sur le réseau xPL ensuite)

import sys, serial
from time import time
from binascii import hexlify
import Queue
import threading

class serialHandler(threading.Thread):


    def __init__(self,serial_port_no):
        #invoke constructor of parent class
        threading.Thread.__init__(self)
        #TODO add parameters for the serial port (number should be enought)
        self._reliable=1
        self._send_queue=Queue.Queue()
        self._receive_queue=Queue.Queue()
        #serial port init
        self.__myser = serial.Serial(serial_port_no, 9600, timeout=0.4, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, xonxoff=0) #, rtscts=1)
        print "port serie ouvert" + self.__myser.portstr

    def send(self,plcbus_frame):
        #seems to work OK, but is all this retransmission process needed ?
        #à cet endroit les messages sont formatés correctement, il faut juste les envoyer sur le port série
        for i in range(2):
            self.__myser.write(plcbus_frame.decode("hex"))

        print 'emis 2 fois'
        #on l'envoie plusieurs fois si on ne reçoit pas d'ACK	
        if self._reliable:
            ACK_received=0
            #like a timer, does not wait for more than 2seconds for example		
            time1=time()
            print "time1", time1
            while 1:
                time2=time()
                print "time2", time2
                while 1:
                    message=self.__myser.read(size=9) #timeout should be 40ms
                    #put message in _received_queue		#in order to be sent on the xPL network
                    print "recu " + hexlify(message)
                    if(message and self._is_ack(message,plcbus_frame)): #check if the received frame is the waited ACK
                        ACK_received=1
                        print "ACK received"
                    
                    if (ACK_received==1 or time2 + 0.2 < time()): break #200ms
                #end of do while
                print "end of while ack", ACK_received	
                if(ACK_received==0):
                    #we waited 200ms and not received ACK, try again
                    print "sending again message"
                    self.__myser.write(plcbus_frame.decode("HEX"))	

                if(ACK_received==1 or time1 + 2 < time()): break			#2s
            #end of second do while

    def receive(self):
        #not tested
        message=self.__myser.read(9)
        #put frame_PLCbus in receivedqueue
        if(message):
            print "recu " + hexlify(message)
            self._receive_queue.put(hexlify(message))
    def _is_ack(self,m1, m2):
        #TODO check if m1 and m2 have same user code, house code and device code
        #check the ACK bit
        #return m1 & 8192 #20 00 in hexa does not work because type(m1) is string...
        return 1

    #def serial_handler_main_thread(self):
    def run(self):
        #not implemented nor tester (queues not yet implemented)
        #on envoie tout, normalement ça ne prend pas longtemps
        while 1:
            #print "check to send"
            while(self._send_queue.empty() == False):
                #print "something to send"
                message=self._send_queue.get()
                self.send(message) #avec retransmission ou pas

            #print "receiving"
            self.receive() #genre 100-200ms de timeout

    def add_to_send_queue(self, trame):
        self._send_queue.put(trame)	

    def get_from_receive_queue(self):
        trame=self._receive_queue.get_nowait()
        return trame

    def dummytest(self):
        print 'ok'

#a=serialHandler()
#a.start()
#pas sur du contenu des trames suivantes
#trame='0205000000000003'
#trame='0205000102000003'#A2 on
#trame='0205000002000003'#A1 on
#trame='0205450122000003' #A2 on ack asked
#trame='020545E302000003' #B1 on
#a.add_to_send_queue(trame)

#a.get_from_receive_queue() #attention, bloquant


#je n'ai pas gere comment quitter
#a.join()



#trame='0205FF0123000003' #A2 off ack asked
#trame='020500000F000003' #Status checking
#trame='0205000018000003' #get signal strength

