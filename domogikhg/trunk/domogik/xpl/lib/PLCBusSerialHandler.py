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
#Threaded class to handle serial port in PLCbus communication
#Send PLCBUS frames when available in the send_queue and manage retransmission if needed
#Put received frames in the receveive_queue (to be sent on the xPL network

    
import sys, serial
import time 
from binascii import hexlify
import Queue
import threading

class serialHandler(threading.Thread):


#TODO add logger and/or debug instead of print

    def __init__(self,serial_port_no):
        #invoke constructor of parent class
        threading.Thread.__init__(self)
        self._send_queue=Queue.Queue()
        self._receive_queue=Queue.Queue()
        self._answer_queue=Queue.Queue()
        
        self._need_answer=["1D","1C"] 
        #serial port init
        self.__myser = serial.Serial(serial_port_no, 9600, timeout=0.4, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, xonxoff=0) #, rtscts=1)
        print "PLCBUS Serial port open " + self.__myser.portstr 
        

    def send(self,plcbus_frame):
        #seems to work OK, but is all this retransmission process needed ?
        #frame should already be properly formated.
        for i in range(2):
            self.__myser.write(plcbus_frame.decode("hex"))

        #print 'sent 2 times'
        #Resend if proper ACK not received
        #check for ack pulse 
        if (int(plcbus_frame[8:10],16)>>5) & 1: #ACK pulse bit set to 1
            time.sleep(0.41) #wait a bit, (in the spec it is written 400ms, in a forum it is stated that it should be a typo and should be 40ms
            ACK_received=0
            #like a timer, does not wait for more than 2seconds for example        
            time1=time.time()
            #print "time1", time1
            while 1:
                time2=time.time()
                #print "time2", time2
                while 1:
                    message=self.__myser.read(size=9) #timeout should be 40ms
                    #put message in _received_queue        #in order to be sent on the xPL network
                    print "recu " + hexlify(message)
                    if(message and self._is_ack(message,plcbus_frame)): #check if the received frame is the waited ACK
                        ACK_received=1
                        #print "ACK received"
                    
                    if (ACK_received==1 or time2 + 0.2 < time.time()): break #200ms
                #end of do while
                if(ACK_received==0):
                    #we waited 200ms and not received ACK, try again
                    print "sending again message"
                    self.__myser.write(plcbus_frame.decode("HEX"))    

                if(ACK_received==1 or time1 + 2 < time.time()): break            #2s
            #end of second do while

    def receive(self):
        #not tested
        message=self.__myser.read(9)
        #put frame_PLCbus in receivedqueue
        if(message):
            m_string=hexlify(message)
            print "recu " + m_string
            #if message is likely to be an answer, put it in the right queue
            if self._is_answer(m_string):
                self._answer_queue.put(m_string)
            else:
                self._receive_queue.put(m_string)



    def _is_ack(self,m1, m2):
        #check the ACK bit
        #print "ACK check " + m1.encode('HEX') +" " + m2
        #check house code and user code in hexa string format like '45E0'
        if(m1.encode('HEX')[4:8].upper()==m2[4:8].upper()):
            #print "housecode and usercode OK"
            return (int(m1.encode('HEX')[14:16],16) & 0x20) #test only one bit
        return 0

    def _is_answer(self,message):
        #if command is in answer required list (not ACK required, it's different)
        #if R_ID_SW bit set
        #maybe pass this list to the _init_ of this handler to make it compatible with other protocols
        if( (int(message[14:15],16)>>2 & 1) and   message[8:10].upper() in self._need_answer):
            return True
        return False

    #serial handler main thread
    def run(self):
        while 1:
            #print "check to send"
            while(self._send_queue.empty() == False):
                #print "something to send"
                message=self._send_queue.get()
                self.send(message) 
        
            #print "receiving"
            self.receive() 

    def add_to_send_queue(self, trame):
        self._send_queue.put(trame)    
    
    def get_from_receive_queue(self):
        trame=self._receive_queue.get_nowait()
        return trame

    def get_from_answer_queue(self):
        trame=self._answer_queue.get(True,2) #do not wait for more than 2s
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

