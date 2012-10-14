# -*- coding: utf-8 -*-

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

Get event from PLCBUS and send them on xPL

Implements
==========

- serialHandler

@author: Yoann HINARD <yoann.hinard@gmail.com>
@copyright: (C) 2007-2012 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

import sys
import time
from binascii import hexlify
import Queue
import threading
import mutex
import datetime
import serial



class serialHandler(threading.Thread):
    """
    Threaded class to handle serial port in PLCbus communication
    Send PLCBUS frames when available in the send_queue and manage
    retransmission if needed
    Put received frames in the receveive_queue (to be sent on the xPL network
    """

    def __init__(self, serial_port_no, command_cb, message_cb):
        """ Initialize threaded PLCBUS manager
        Will handle communication to and from PLCBus 
        @param serial_port_no : Number or path of the serial port 
        @param command_cb: callback called when a command has been succesfully sent
        @param message_cb: called when a message is received from somewhere else on the network
        For these 2 callbacks, the param is sent as an array
        """
        threading.Thread.__init__(self)
        #invoke constructor of parent class
        self._ack = threading.Event() #Shared list between reader and writer
        self._need_answer = ["1D", "1C"]
        self._stop = threading.Event()
        self._has_message_to_send = threading.Event()
        #serial port init
        self.__myser = serial.Serial(serial_port_no, 9600, timeout = 0.4,
                parity = serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE,
                xonxoff = 0) #, rtscts=1)
#        self._want_lock = threading.Event()
#        self._mutex = mutex.mutex()
        self._send_queue = Queue.Queue()
        self._cb = command_cb
        self._msg_cb = message_cb
        #self._reader = self.__Reader(self.__myser, self._want_lock, self._mutex, self._ack, message_cb)
        #self._reader.start()
        #self._writer = self.__Writer(self.__myser, self._want_lock, self._mutex, self._ack, command_cb, self._reader)
        #self._writer.start()

    def _send(self, plcbus_frame):
        #Resend if proper ACK not received
        #check for ack pulse
        explicit_frame = self.explicit_message(plcbus_frame)
        if (int(plcbus_frame[8:10], 16) >> 5) & 1: #ACK pulse bit set to 1
            #The ACK message take only 10ms + 10ms to bring it back to the computer.
            #Anyway, it seems that the mean time before reading the ack is about 
            #0.6s . Because there is another sleep in the loop, this sleep is only 0.3s
         #   time.sleep(0.3)
            ACK_received = 0
            # like a timer, does not wait for more than 2seconds for example
            time1 = time.time()
            while not self._stop.isSet():
                #The ack message is sent immediately after the message has been received 
                #and transmission time is 20mS (10ms for message propagation to adapter,
                #and 10ms between adapter and computer
                #We sleep 20ms between each check
                self.needs_ack_for(plcbus_frame)
                self._basic_write(plcbus_frame)
                time.sleep(0.6)
                print("time before wait : %s" % time.time())
                for i in range(3):
                    self.receive()
                    if self._ack.isSet():
                        print("got ack in first read")
                        break
                print("time after wait : %s" % time.time())
                if self._ack.isSet():
                    print(plcbus_frame + " : Ack set")
                    ACK_received = 1
                    self._ack.clear()
                    self._cb(self.explicit_message(plcbus_frame))
                    break

                if (ACK_received == 1):
                    break
                elif(time1 + 3.1 < time.time()):
                    print("WARN : Message %s sent, but ack never received" % plcbus_frame)
                    break #2s
        elif explicit_frame["d_command"] not in ['GET_ALL_ID_PULSE', 'GET_ALL_ON_ID_PULSE']:
            #No ACK asked, we consider that the message has been correctly sent
            self._basic_write(plcbus_frame)
            self._cb(explicit_frame)
        else:
            self._basic_write(plcbus_frame)

    def _basic_write(self, frame):
        """Write a frame on serial port
        This method should only be called as mutex.lock() parameter
        @param frame : The frame to write 
        """
        print("SEND : %s" % frame)
        self.__myser.write(frame.decode("HEX"))

    def add_to_send_queue(self, trame):
        print("add_to_send_queue : %s" % trame)
        self._send_queue.put(trame)

    def needs_ack_for(self, frame):
        """ Called by the Writer to let Reader knows that a ACK is waited
        it will set the internal _waited_ack until the ack is received 
        @param frame : the plcbus frame
        """
        self._waited_ack = frame

    def _is_ack_for_message(self, m1, m2):
        #check the ACK bit
        #print("ACK check " + m1.encode('HEX') +" " + m2)
        #check house code and user code in hexa string format like '45E0'
        if(m1[4:8].upper() == m2[4:8].upper()) and (m1[8:10].upper() == m2[8:10].upper()): #Compare user code + home unit
            #print("housecode and usercode OK")
            return (int(m1[14:16], 16) & 0x20) #test only one bit
        return False

    def _is_answer(self, message):
        # if command is in answer required list (not ACK required, it's
        # different)
        # if R_ID_SW bit set
        # maybe pass this list to the _init_ of this handler to make it
        # compatible with other protocols
        if((int(message[14:15], 16) >> 2 & 1) and message[8:10].upper() in
                ["1C","1D"]):
            return True
        return False

    def explicit_message(self, message):
        """ Parse a frame 
        """
        cmdplcbus = {
        '00': 'ALL_UNITS_OFF',
        '01': 'ALL_LIGHTS_ON',
        '22': 'ON', #ON and ask to send ACK (instead of '02')
        '23': 'OFF', #OFF and send ACK
        '24': 'DIM',
        '25': 'BRIGHT',
        '06': 'ALL_LIGHTS_OFF',
        '07': 'ALL_USER_LTS_ON',
        '08': 'ALL_USER_UNIT_OFF',
        '09': 'ALL_USER_LIGHT_OFF',
        '2a': 'BLINK',
        '2b': 'FADE_STOP',
        '2c': 'PRESET_DIM',
        '0d': 'STATUS_ON',
        '0e': 'STATUS_OFF',
        '0f': 'STATUS_REQUEST',
        '30': 'REC_MASTER_ADD_SETUP',
        '31': 'TRA_MASTER_ADD_SETUP',
        '12': 'SCENE_ADR_SETUP',
        '13': 'SCENE_ADR_ERASE',
        '34': 'ALL_SCENES_ADD_ERASE',
        '15': 'FOR FUTURE',
        '16': 'FOR FUTURE',
        '17': 'FOR FUTURE',
        '18': 'GET_SIGNAL_STRENGTH',
        '19': 'GET_NOISE_STRENGTH',
        '1a': 'REPORT_SIGNAL_STREN',
        '1b': 'REPORT_NOISE_STREN',
        '1c': 'GET_ALL_ID_PULSE',
        '1d': 'GET_ALL_ON_ID_PULSE',
        '1e': 'REPORT_ALL_ID_PULSE',
        '1f': 'REPORT_ONLY_ON_PULSE'}
        home = "ABCDEFGHIJKLMNOP"
        r = {}
        r["start_bit"] = message[0:2]
        r["data_length"] = int(message[2:4])
        int_length = int(message[2:4])*2
        r["data"] = message[4:4+int_length]
        r["d_user_code"] = r["data"][0:2]
        r["d_home_unit"] = "%s%s" % (home[int(r["data"][2:3], 16)],int(r["data"][3:4], 16)+1)
        r["d_command"] = cmdplcbus[r["data"][4:6]]
        r["d_data1"] = int(r["data"][6:8],16)
        r["d_data2"] = int(r["data"][8:10],16)
        if r["data_length"] == 6:
            r["rx_tw_switch"] = r["data"][11:]
        r["end_bit"] = message[-2:]
        return r

    def receive(self):
        #Avoid to wait if there is nothing to read
#        try:
        if self._stop.isSet():
            return
        if self.__myser.inWaiting() < 9:
            time.sleep(0.4)
            return
        while self.__myser.inWaiting() >= 9:
            message = self.__myser.read(9) #wait for max 400ms if nothing to read
#        except IOError:
#            pass
            if(message):
                m_string = hexlify(message)
                #self.explicit_message(m_string)
                #if message is likely to be an answer, put it in the right queue
                #First we check that the message is not from the adapter itself
                #And simply ignore it if it's the case 
                print("str : %s" % m_string)
                if self._is_from_myself(m_string):
                    print("from myself")
                    return
                if self._is_answer(m_string):
                    print("ANSWER : %s" % m_string)
                    self._cb(self.explicit_message(m_string))
                elif self._is_ack(m_string):
                    print("IS ACK : %s, waited ack : %s" % (m_string, self._waited_ack))
                    if (self._waited_ack != None) and self._is_ack_for_message(m_string, self._waited_ack):
                        self._waited_ack = None
                        self._ack.set()
                else:
                    print("QUEUE : %s" % m_string)
                    self._cb(self.explicit_message(m_string))

    def stop(self):
        """ Ask the thread to stop, 
        will only set a threading.Event instance
        and close serial port
        """
        self._stop.set()
        self.__myser.close()

    def run(self):
        #serial handler main thread
#        self._mutex.testandset()
        while not self._stop.isSet():
            #The Event _has_message_to_send is only used to optimize
            #The test isSet is much faster than the empty() test 
            #If _has_message_to_send is locked, then there is at least 1 lock(function)
            #in the queue, so the unlock() will just do this call, 
            #not really unlock the mutex.
            try:
                item = self._send_queue.get_nowait()
            except Queue.Empty:
                pass
            else:
                self._send(item)
#                self._mutex.unlock()
#                self._mutex.testandset()
            #print("receiving")
            self.receive()

    def _is_ack(self, message):
        """ Check if a message is an ack 
            @param message : message to check
        """
        return int(message[14:16], 16) & 0x20

    def _is_from_myself(self, message):
        """ Check if a message is sent by the adapter itself
            @param message : message to check
        """
        return int(message[14:16], 16) & 0x10

#a = serialHandler()
#a.start()
#pas sur du contenu des trames suivantes
#trame = '0205000000000003'
#trame = '0205000102000003'#A2 on
#trame = '0205000002000003'#A1 on
#trame = '0205450122000003' #A2 on ack asked
#trame = '020545E302000003' #B1 on
#a.add_to_send_queue(trame)

#a.get_from_receive_queue() #attention, bloquant


#je n'ai pas gere comment quitter
#a.join()



#trame = '0205FF0123000003' #A2 off ack asked
#trame = '020500000F000003' #Status checking
#trame = '0205000018000003' #get signal strength
