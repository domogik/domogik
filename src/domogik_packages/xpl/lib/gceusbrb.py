#!/usr/bin/python
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

plugin purpose
==============

GCE USB RelayBoard control with COM Port

Implements
==========

- Based on SamsungTv & IPX800 plugin from Fritz <fritz.smh@gmail.com> @ (C) 2007-2009 Domogik project
"""

import binascii
import serial
import traceback
import time
import sys

# status
RB_LED_HIGH = "1"
RB_LED_LOW = "0"

COMMANDS = {
"Relay1_ON" : "RLY11", # Power On Relay 1
"Relay1_OFF" : "RLY10", # Power Off Relay 1
"Relay2_ON" : "RLY21", # Power On Relay 2
"Relay2_OFF" : "RLY20", # Power Off Relay 2
"Relay3_ON" : "RLY31", # Power On Relay 3
"Relay3_OFF" : "RLY30", # Power Off Relay 3
"Relay4_ON" : "RLY41", # Power On Relay 4
"Relay4_OFF" : "RLY40", # Power Off Relay 4
"Relay5_ON" : "RLY51", # Power On Relay 5
"Relay5_OFF" : "RLY50", # Power Off Relay 5
"Relay6_ON" : "RLY61", # Power On Relay 6
"Relay6_OFF" : "RLY60", # Power Off Relay 6
"Relay7_ON" : "RLY71", # Power On Relay 7
"Relay7_OFF" : "RLY70", # Power Off Relay 7
"Relay8_ON" : "RLY81", # Power On Relay 8
"Relay8_OFF" : "RLY80", # Power Off Relay 8
"Memory_OFF" : "M0", # Relay memory Off
"Memory_ON" : "M1", # Relay memory On
"CheckS" : "?RLY", # Check States Return something like 00000010 (means everything is off except Relay number 7 
}

class RelayboardusbException(Exception):  
    """                                                                         
    Relayboard USB control exception                                                           
    """                                                                         
                                                                                
    def __init__(self, value):                                                  
        Exception.__init__(self)
        self.value = value                                                      
                                                                     
    def __str__(self):                                                          
        return repr(self.value)           


class Relayboardusb:
    """ ex. SamsungTV Control Relayboard USB
    """

    def __init__(self, log, callback):
        """ Init Relayboard USB controller
        """
        self._log = log
        self._callback = callback
        self._relayboardusb = None
        self.rb_led = {}  # relays
        self.rb_old_led = {}  # relays
        self.name = ""

    def open(self, device, name):
        """ Open COM Port
            @param device : serial port connected to RelayBoard
        """
        self.name = name
        try:
            print("Try to open RelayBoard device : %s" % device)
            self._relayboardusb = serial.Serial(device, 9600, 
                                parity=serial.PARITY_NONE,
                                stopbits=serial.STOPBITS_ONE,
                                xonxoff=serial.XOFF,
                                timeout=1)
            # timeout = 1 : wait 1 second for timeout when reading serial port
            print("RelayBoard device opened")
            self._relayboardusb.write("M1")
            print("RelayBoard Memory Mode M1 activated")
        except:
            error = "Error while opening Relayboard device : %s. Check if it is the good device or if you have the good permissions on it." % device
            raise RelayboardusbException(error)

    def get_status(self):
        """ Get status of all 8 Relays
        """
        idx = 1
        print("Send command ?RLY")
        cmd = "?RLY"
        self._relayboardusb.write("%s" % cmd)
        print("Sleep 1")
        time.sleep(1) # sleep
        res = self._relayboardusb.readline()
        print("res=%s" % res)
        if res != "?":
            print("Command is OK") # check status of the command
            # compute the result : 00000010
            for idx in range(1,9):
                if res[idx:idx+1]==RB_LED_HIGH:
                    #print ("HIGH rb_led[%s]=result" % (idx))
                    self.rb_led[idx]=RB_LED_HIGH
                else:
                    #print ("LOW else rb_led[%s]=result" % (idx))
                    self.rb_led[idx]=RB_LED_LOW
            for idx in self.rb_led:
               print(" - led%s : %s" % (idx, self.rb_led[idx]))
            return True
        else:
            print("Error on command [%s]" % res)
            return False

    def get_status_for_helper(self):
        """ Return status for helper
        """
        status = []
        status.append("List of relay :")
        for idx in self.rb_led:
            status.append(" - led%s : %s" % (idx, self.rb_led[idx]))
        status.append("List of digital input :")
        return status

    def send(self, cmd_alias, param = None):
        """ Send command code associated to alias to RelayBoard
            @param cmd_alias : alias Relay1_ON
            @param param : command parameter 
        """
        print("Call command '%s' with parameter '%s'" % (cmd_alias, param))
        if not cmd_alias in COMMANDS:
            print("Command not known : '%s'" % cmd_alias)
            return False
        cmd = self.generate_command(COMMANDS[cmd_alias], param)
        print("Code for command : '%s'" % cmd)
        #data = binascii.unhexlify(cmd) # Convert to hex ?
        #self._samsung.write("%s" % data)
        self._relayboardusb.write("%s" % cmd)
        #res = binascii.hexlify(self._samsung.readline()) # ? keep the readline for checkS cmd !
        res = self._relayboardusb.readline()
        print("res=%s" % res)
        if res != "?":
            print("Command is OK") # check status of the command
            return True
        else:
            print("Error on command [%s]" % res)
            return False

    def send_change(self, data):
        """ Send changes on xpl
            @param data : dictionnay with data
            we send HIGH or LOW
        """
        # if no callback defined (used by helper for example), don't send changes
        if self._callback == None:
            return

        self._log.debug("Status changed : %s" % data)
        #print("Status changed : %s" % (data))
        device = "%s-%s%s" % (self.name, data['elt'], data['num'])

        # translate values
        if data['elt'] == "led" and data['value'] == RB_LED_HIGH:
            current = "HIGH"
        elif data['elt'] == "led" and data['value'] == RB_LED_LOW:
            current = "LOW"
        else:
            current = data['value']

        # translate type
        #if data['elt'] == "led":
        #    elt_type = 'output'
        elt_type = 'output'    
        print("%s-%s(%s)-%s"  % (device, current, data['value'], elt_type))
        self._callback(device, current, elt_type)


    def set_relay(self, num, state):
        """" Set relay <num> to state <state>
             @param num : relay number (1,2,3,4,5,6,7,8)
             @param state : HIGH, LOW
        """
        # we get instant status of board
        self.get_status()
        actual = self.rb_led[num]
        # do we need to change status ?
        if actual == RB_LED_HIGH and state == "HIGH" or actual == RB_LED_LOW and state == "LOW":
            # no need to change status
            self._log.debug("No need to change 'led%s' status to '%s'" % (num, state))
            #print("No need to change 'led%s' status to '%s'" % (num, state))
            # no change but you should send a xpl-trig to tell that 
            # the order was received
            self.send_change({'elt' : 'led',
                              'num' : num,
                              'value' : actual})
            return

        print("Set Relay '%s' with state '%s'" % (num, state))
        if state == "LOW":
            cmd = ("RLY%s%s" % (num,0))
            self.send_change({'elt' : 'led','num' : num,'value' : RB_LED_LOW})
        else:
            cmd = ("RLY%s%s" % (num,1))
            self.send_change({'elt' : 'led','num' : num,'value' : RB_LED_HIGH})
        print("Code for command : '%s'" % cmd)
        self._relayboardusb.write("%s" % cmd)
        res = self._relayboardusb.readline()
        print("res=%s" % res)
        if res != "?":
            print("Command is OK") # check status of the command
        else:
            print("Error on command [%s]" % res)

    def close(self):
        """ Close COM Port
        """
        self._relayboardusb.close()

if __name__ == "__main__":
    my_tv = Relayboardusb(None,None)
    my_tv.open("/dev/ttyUSB0","rb1")
    my_tv.get_status()
    my_tv.set_relay(4,"HIGH")
    my_tv.set_relay(5,"LOW")
    my_tv.close()


