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

Plugin purpose
==============

New Usb RFXCOM model support

Notice : as detailed in "_process_58" function, datetime sensors are
         not handled in this plugin
         
Implements
==========

- RfxcomUsb

@author: Fritz <fritz.smh@gmail.com>
@copyright: (C) 2007-2009 Domogik project
@license: GPL(v3)
@organization: Domogik
"""


# TODO : put all global tables in concerned functions

# TODO : hbeat (app and request) implementation
#        log.basic implementation
#        x10.basic
#        ac.basic
#        x10.security
#        remote.basic
#        control.basic


import binascii
import serial
import traceback
import threading
from Queue import Queue, Empty, Full

WAIT_BETWEEN_TRIES = 1

HUMIDITY_STATUS = {
  "0x00" : "dry",
  "0x01" : "comfort",
  "0x02" : "normal",
  "0x03" : "wet",
}

FORECAST = {
  "0x00" : "unknown",
  "0x01" : "sunny",
  "0x02" : "partly cloudy",
  "0x03" : "cloudy",
  "0x04" : "rain",
}

# TODO : add a "0" after the x ?
THERMOSTAT_MODE = {
  "0x0" : "heating",
  "0x1" : "cooling",
}

# TODO : add a "0" after the x ?
THERMOSTAT_STATUS = {
  "0x0" : "no status available",
  "0x1" : "demand",
  "0x2" : "no demand",
  "0x3" : "initializing",
}

# TODO : add a "0" after the x ?
HEXA_TO_HOUSECODE = {
  "0x0" : "A",
  "0x1" : "B",
  "0x2" : "C",
  "0x3" : "D",
  "0x4" : "E",
  "0x5" : "F",
  "0x6" : "G",
  "0x7" : "H",
  "0x8" : "I",
  "0x9" : "J",
  "0xA" : "K",
  "0xB" : "L",
  "0xD" : "M",
  "0xD" : "N",
  "0xE" : "O",
  "0xF" : "P",
}

# TODO : add a "0" after the x ?
HOUSECODE_TO_HEXA = {
  "A" : "00",
  "B" : "01",
  "C" : "02",
  "D" : "03",
  "E" : "04",
  "F" : "05",
  "G" : "06",
  "H" : "07",
  "I" : "08",
  "J" : "09",
  "K" : "0A",
  "L" : "0B",
  "M" : "0D",
  "N" : "0D",
  "O" : "0E",
  "P" : "0F",
}

X10_NINJA_CMD = {
  "left" : "00",
  "right" : "01",
  "up" : "02",
  "down" : "03",
  "p1" : "04",
  "prog_p1" : "05",
  "p2" : "06",
  "prog_p2" : "07",
  "p3" : "08",
  "prog_p3" : "09",
  "p4" : "0A",
  "prog_p4" : "0B",
  "center" : "0C",
  "prog_center" : "0D",
  "sweep" : "0E",
  "prog_sweep" : "0F",
 }
 
RFXSENSOR_MSG = {
  "0001" : "sensor addresses incremented",
  "0002" : "battery low detected",
  "0081" : "no 1-wire device connected",
  "0082" : "1-Wire ROM CRC error",
  "0083" : "1-Wire device connected is not a DS18B20 or DS2438",
  "0084" : "no end of read signal received from 1-Wire device",
  "0085" : "1-Wire scratchpad CRC error ",
}

REMOTE_X10_RF = {
  "0x02" : "0",
  "0x12" : "8",
  "0x22" : "4",
  "0x38" : "Rewind",
  "0x3A" : "Info",
  "0x40" : "CHAN+",
  "0x42" : "2",
  "0x52" : "Ent",
  "0x60" : "VOL+",
  "0x62" : "6",
  "0x63" : "Stop",
  "0x64" : "Pause",
  "0x70" : "Cursor-left",
  "0x71" : "Cursor-right",
  "0x72" : "Cursor-up",
  "0x73" : "Cursor-down",
  "0x74" : "Cursor-up-left",
  "0x75" : "Cursor-up-right",
  "0x76" : "Cursor-down-right",
  "0x77" : "Cursor-down-left",
  "0x78" : "left mouse",
  "0x79" : "left mouse-End",
  "0x7B" : "Drag",
  "0x7C" : "right mouse",
  "0x7D" : "right mouse-End",
  "0x82" : "1",
  "0x92" : "9",
  "0xA0" : "MUTE",
  "0xA2" : "5",
  "0xB0" : "Play",
  "0xB6" : "Menu",
  "0xB8" : "Fast Forward",
  "0xBA" : "A+B",
  "0xC0" : "CHAN-",
  "0xC2" : "3",
  "0xC9" : "Exit",
  "0xD1" : "MP3",
  "0xD2" : "DVD",
  "0xD3" : "CD",
  "0xD4" : "PC / Shift-4",
  "0xD5" : "Shift-5",
  "0xD6" : "Shift-Ent",
  "0xD7" : "Shift-Teletext",
  "0xD8" : "Text",
  "0xD9" : "Shift-Text",
  "0xE0" : "VOL-",
  "0xE2" : "7",
  "0xF2" : "Teletext",
  "0xFF" : "Record",
}

REMOTE_ATI_WONDER = {
  "0x003" : "A",
  "0x013" : "B",
  "0x023" : "power",
  "0x033" : "TV",
  "0x043" : "DVD",
  "0x053" : "?",
  "0x063" : "Guide",
  "0x073" : "Drag",
  "0x083" : "VOL+",
  "0x093" : "VOL-",
  "0x0A3" : "MUTE",
  "0x0B3" : "CHAN+",
  "0x0C3" : "CHAN-",
  "0x0D3" : "1",
  "0x0E3" : "2",
  "0x0F3" : "3",
  "0x103" : "4",
  "0x113" : "5",
  "0x123" : "6",
  "0x133" : "7",
  "0x143" : "8",
  "0x153" : "9",
  "0x163" : "txt",
  "0x173" : "0",
  "0x183" : "snapshot ESC",
  "0x193" : "C",
  "0x1A3" : "^",
  "0x1B3" : "D",
  "0x1C3" : "TV/RADIO",
  "0x1D3" : "<",
  "0x1E3" : "OK",
  "0x1F3" : ">",
  "0x203" : "<-",
  "0x213" : "E",
  "0x223" : "v",
  "0x233" : "F",
  "0x243" : "Rewind",
  "0x253" : "Play",
  "0x263" : "Fast forward",
  "0x273" : "Record",
  "0x283" : "Stop",
  "0x293" : "Pause",
  "0x2C3" : "TV",
  "0x2D3" : "VCR",
  "0x2E3" : "RADIO",
  "0x2F3" : "TV Preview",
  "0x303" : "Channel list",
  "0x313" : "Video Desktop",
  "0x323" : "red",
  "0x333" : "green",
  "0x343" : "yellow",
  "0x353" : "blue",
  "0x363" : "rename TAB",
  "0x373" : "Acquire image",
  "0x383" : "edit image",
  "0x393" : "Full screen",
  "0x3A3" : "DVD Audio",
  "0x703" : "Cursor-left",
  "0x713" : "Cursor-right",
  "0x723" : "Cursor-up",
  "0x733" : "Cursor-down",
  "0x743" : "Cursor-up-left",
  "0x753" : "Cursor-up-right",
  "0x763" : "Cursor-down-right",
  "0x773" : "Cursor-down-left",
  "0x783" : "V",
  "0x793" : "V-End",
  "0x7C3" : "X",
  "0x7D3" : "X-End",
}


AC_CMND = {
  "00" : "off",
  "01" : "on",
  "02" : "preset",
  "03" : "off",
  "04" : "on",
  "05" : "Set group level",
}

#TODO : X10 RF Remote
#       ATI Remote Wonder
#       ATI Remote Wonder Plus
#       Medion Remote
#       Harrison address conversion to switch settings
#       Flamingo, AB400, IMPULS switch settings
#       


# TODO : manage correctly seqnbr (for read and write)

class RfxcomException(Exception):
    """
    Rfxcom exception
    """

    def __init__(self, value):
        Exception.__init__(self)
        self.value = value

    def __str__(self):
        return repr(self.value)


class RfxcomUsb:
    """ Rfxcom Usb librairy
    """

    def __init__(self, log, callback, stop):
        """ Init object
            @param log : log instance
            @param callback : callback
            @param stop : 
        """
        self._log = log
        self._callback = callback
        self._stop = stop
        self._rfxcom = None
        # TODO : how to get proper value ?
        self.seqnbr = 0

        # Queue for writing packets to Rfxcom
        self.write_rfx = Queue()
        self.rfx_response = Queue()

        # Thread to process queue
        write_process = threading.Thread(None,
                                         self.write_daemon,
                                         "write_packets_process",
                                         (),
                                         {})
        write_process.start()


    def open(self, device):
        """ Open RFXCOM device
            @param device : RFXCOM device (/dev/ttyACMx)
        """
        try:
            self._log.info("Try to open RFXCOM : %s" % device)
            self._rfxcom = serial.Serial(device, 38400)
            #                          timeout=1)

            self._log.info("RFXCOM opened")
        except:
            error = "Error while opening RFXCOM : %s. Check if it is the good device or if you have the good permissions on it." % device
            raise RfxcomException(error)

    def close(self):
        """ close RFXCOM
        """
        self._log.info("Close RFXCOM")
        try:
            self._rfxcom.close()
        except:
            error = "Error while closing device"
            raise RfxcomException(error)
            
    def write_packet(self, data, trig_msg):
        """ Write command to rfxcom
            @param data : command without length
            @param trig_msg : xpl-trig msg to send if success
        """
        length = len(data)/2
        packet = "%02X%s" % (length, data.upper())

        # Put message in write queue
        seqnbr = gh(packet, 2)
        self.write_rfx.put_nowait({"seqnbr" : seqnbr, 
                                   "packet" : packet,
                                   "trig_msg" : trig_msg})

    def write_daemon(self):
        """ Write packets in queue to RFXCOM and manager errors to resend them
            This function must be launched as a thread in backgroun
 
            How it works (actually solution 2) :

            Solution 1 : 
        
            The sequence number is not used by the transceiver so you can leave it zero if you want. But it can be used in your program to which ACK/NAK message belongs to which transmit message.
            You need to keep the messages in a buffer until they are acknowledged by an ACK. If you got a NAK you have to resend a message.
            For example:
            Transmit message 1
            Transmit message 2
            Transmit message 3
    
            Received ACK 1
            Received NAK 2
            Received ACK 3
    
            Now you know that message number 2 is not correct processed and you send again:
            Transmit message 2
            Received ACK 2

            Solution 2 : 
    
            An easier way is to transmit a message and wait for the acknowledge before you transmit the next command:
            Transmit message 1
            Receive ACK 1
            Transmit message 2
            Receive NAK 2
            Transmit message 2
            Receive ACK 2
            Transmit message 3
            Receive ACK 3
        """
        print("Start write_rfx thread")
        # To test, see RFXCOM email from 17/10/2011 at 20:22 
        
        # infinite
        while not self._stop.isSet():

            # Wait for a packet in the queue
            data = self.write_rfx.get(block = True)
            seqnbr = data["seqnbr"]
            packet = data["packet"]
            trig_msg = data["trig_msg"]
            print("Get from Queue : %s > %s" % (seqnbr, packet))
            self._rfxcom.write(binascii.unhexlify(packet))

            # TODO : read in queue in which has been stored data readen from rfx
            loop = True
            while loop == True:
                res = self.rfx_response.get(block = True)
                if res["status"] == "NACK":
                    self.debug.warning("Failed to write. Retry in %s : %s > %s" % (WAIT_BETWEEN_TRIES, seqnbr, packet))
                    sleep(WAIT_BETWEEN_TRIES)
                    self._rfxcom.write(binascii.unhexlify(packet))
                else:
                    print("Command succesfully sent")
                    loop = False
            
    def get_seqnbr(self):
        """ Return seqnbr and then increase it
        """
        ret = self.seqnbr
        if ret == 255:
            ret = 0
        else:
            self.seqnbr += 1
        return "%02x" % ret
            
    def xplcmd_control_basic(msg_device, msg_type, msg_current):
        """ Handle control.basic xpl commande messages
        """
        # Type 0x28 : X10 Ninja/Robocam
        if type.lower() == "ninja":
            self.command_28(device = msg_device,
                             current = msg_current)
        
        # TODO : finish
        pass


    def listen(self, stop):
        """ Start listening to Rfxcom
        @param stop : an Event to wait for stop request
        """
        # listen 
        self._log.info("Start listening RFXCOM")
        # First, ask for hardware informations
        #TODO : call command_00 with appropriate parameter to request status
        # infinite
        try:
            while not stop.isSet():
                self.read()
        except serial.SerialException:
            error = "Error while reading rfxcom device (disconnected ?) : %s" % traceback.format_exc()
            print(error)
            self._log.error(error)
            # TODO : raise for using self.force_leave() in bin ?
            return

    def read(self):
        """ Read Rfxcom device once
            Wait for a byte. It will give message's length
            Then, read message
        """
        # We wait for a message (and its size)
        data_len = self._rfxcom.read()
        hex_data_len = binascii.hexlify(data_len)
        int_data_len = int(hex_data_len, 16)
        print("----------------------------")
        print("LENGTH = %s" % int_data_len)

        if int_data_len != 0:
            # We read data
            data = self._rfxcom.read(int_data_len)
            hex_data = binascii.hexlify(data)
            print("DATA = %s" % hex_data)

            # Process data
            self._process(hex_data)


    def _process(self, data):
        """ Process RFXCOM data
            @param data : data read
        """
        type = data[0] + data[1]
        print "TYPE = %s" % type
        try:
            eval("self._process_%s('%s')" % (type, data))
        except AttributeError:
            self._log.warning("No function for type '%s' with data : '%s'" % (type, data))

        
    def command_00(self, data):
        """ Interface Control
        
            !!! TODO !!!
            
            Type : command
            SDK version : 2.04
            Tested : No
        """
        # send command
        # this function should be called at plugin startup
        # log in INFO level
        pass


    def _process_01(self, data):
        """ Interface Response
        
            !!! TODO !!!
            
            Type : sensor
            SDK version : 2.04
            Tested : No
        """
        # process data
        # don't send xpl until helpers are implemented
        # log also the informations in INFO level
        pass

    ### 0x10 : Lighting1
    #TODO
    

    def _process_02(self, data):
        """ Receiver/Transmitter Message
        
            !!! TODO !!!
            
            Type : rfxcom responses
            SDK version : 2.07
            Tested : No
        """
        subtype = gh(data, 1)
        if subtype == "00":
            type = "error"
            message = "Message not used"
        elif subtype == "01":
            type = "response"
        seqnbr = gh(data, 2)
        msg = gh(data, 3)
        if msg == "00":
            message = "ACK, transmit OK"
            status = "ACK"
        elif msg == "01":
            message = "ACK, but transmit started after 3 seconds delay anyway with RF receive data"
            status = "ACK"
        elif msg == "02":
            message = "NAK, transmitter did not lock on the requested transmit frequency"
            status = "NACK"
        else:
            print("Bad response from RFXCOM : %s" % data)
        print("%s : %s" % (status, message))
        self.rfx_response.put_nowait({"seqnbr" : seqnbr, 
                                      "status" : status})
        


    def command_11(self, address, unit, command, level, eu, group, trig_msg):
        """ Type 0x11, Lighting2

            Type : command
            SDK version : 2.07
            Tested : yes

            Remarks :
            - eu != true : Chacon, KlikAanKlikUit, HomeEasy UK, NEXA 
            - eu = true : HomeEasy EU
            - ANSLUT is the same as Chacon. But the address must have a special
              address, not all addresses are accepted in fact. The user has to 
              try addresses and change the lowest address digit until the ANSLUT              responds.
        """
        COMMAND = {"off"    : "00",
                   "on"     : "01",
                   "preset" : "02",
                   "group_off"    : "03",
                   "group_on"     : "04",
                   "group_preset" : "05"}
        # type
        cmd = "11" 
        # subtype
        if eu != True:
            cmd += "00"
        else:
            cmd += "01"
        # Note : ANSLUT not implemented (view remark in function header
        # seqnbr
        cmd += self.get_seqnbr()
        # address
        cmd += "%08x" % int(bin(int(address, 16))+'00', 2)
        # unit code
        cmd += "%02x" % unit
        # cmnd
        if group == True:
            command = "group_" + command
        cmd += COMMAND[command.lower()]
        # level
        cmd += "%02x" % level
        # filler + rssi : 0x00
        cmd += "00"
        
        self._log.debug("Type x11 : write '%s'" % cmd)
        self.write_packet(cmd, trig_msg)


    def _process_11(self, data):
        """ Type 0x11, Lighting2
        
            Type : command/sensor
            SDK version : 2.06
            Tested : No
        """
        subtype = gh(data, 1)
        seqnbr = gh(data, 2)
        # TODO : it is more complexe... see spec !!!!!!!!!!!!!!!!!!
        id = gh(data, 3,4)
        address = "0x%s" %(id)
        unit_code = int(gh(data, 7), 16)
        cmnd = gh(data, 8)
        level = int(gh(data, 9), 16)
        battery = int(gh(data, 7)[0], 16) * 10  # percent
        rssi = int(gh(data, 7)[1], 16) * 100/16 # percent

        if AC_CMND[cmnd] == "preset":
            self._callback("ac.basic",
                       {"address" : address, 
                        "unit" : unit_code,
                        "command" : AC_CMND[cmnd],
                        "level" : level})
        else:
            self._callback("ac.basic",
                       {"address" : address, 
                        "unit" : unit_code,
                        "command" : AC_CMND[cmnd]})
        self._callback("sensor.basic",
                       {"device" : address, 
                        "type" : "battery", 
                        "current" : battery})
        self._callback("sensor.basic",
                       {"device" : address, 
                        "type" : "rssi", 
                        "current" : rssi})
 
    

    ### 0x12 : Lighting3
    #TODO
    

    ### 0x13 : Lighting4
    #TODO
    

    ### 0x18 : Curtain1
    #TODO
    

    ### 0x20 : Security1
    #TODO
    

    ### 0x21 : Security2
    #TODO
    

    def command_28(self, device, current):
        """ X10 Ninja/Robocam

            Type : command
            SDK version : 2.06
            Tested : No
        """
        # type
        cmd = "28" 
        # subtype
        cmd += "00"
        # seqnbr
        cmd += self.get_seqnbr()
        # housecode
        cmd += HOUSECODE_TO_HEXA[device.upper()]
        # cmnd
        cmd += X10_NINJA_CAM[current.lower()]
        # filler + rssi : 0x00
        cmd += "00"
        
        self._log.debug("Type x28 : write '%s'" % cmd)
        # TODO : set trig_msg !!!!!
        self.write_packet(cmd, None)

    ### 0x30 : Remote control and IR
    #TODO
    

    def _process_40(self, data):
        """ Thermostat1
        
            Type : sensor
            SDK version : 2.06
            Tested : No
        """
        subtype = gh(data, 1)
        seqnbr = gh(data, 2)
        id = gh(data, 3,2)
        address = "digimax 0x%s" %(id)
        temp = int(gh(data, 5), 16)
        setpoint = int(gh(data, 6), 16)
        bin_status_mode = gb(data, 7)
        mode = THERMOSTAT_MODE[hexa(get_bit(bin_status_mode, 0))]
        status = THERMOSTAT_STATUS[hexa(get_bit(bin_status_mode, 6, 2))]
        if status == "demand":
            demand = "%s_on" % mode
        elif status == "no demand":
            demand = "%s_off" % mode
        else:
            demand = None
        battery = int(gh(data, 8)[0], 16) * 10  # percent
        rssi = int(gh(data, 8)[1], 16) * 100/16 # percent
 
        # send xPL
        self._callback("sensor.basic",
                       {"device" : address, 
                        "type" : "temp", 
                        "current" : temp, 
                        "units" : "c"})
        if subtype == "00":
            self._callback("sensor.basic",
                       {"device" : address, 
                        "type" : "setpoint", 
                        "current" : setpoint, 
                        "units" : "c"})
        if demand != None:
            self._callback("sensor.basic",
                       {"device" : address, 
                        "type" : "demand", 
                        "current" : demand})
        self._callback("sensor.basic",
                       {"device" : address, 
                        "type" : "battery", 
                        "current" : battery})
        self._callback("sensor.basic",
                       {"device" : address, 
                        "type" : "rssi", 
                        "current" : rssi})


    ### 0x41 : Thermostat2
    #TODO
    

    ### 0x42 : Thermostat3
    #TODO
    

    def _process_50(self, data):
        """ Temperature sensors
        
            Type : sensor
            SDK version : 2.06
            Tested : No
        """
        subtype = gh(data, 1)
        seqnbr = gh(data, 2)
        id = gh(data, 3,2)
        address = "temp%s 0x%s" %(subtype[1], id)
        temp_high = gh(data, 5)
        temp_low = gh(data, 6)
        # first bit = 1 => sign = "-"
        if (int(temp_high, 16) & 0b1000000) == 0b10000000:
            temp = - float((int(temp_low, 16) + 256*(int(bin(temp_high, 16)) & 0b01111111)))/10
        # first bit = 0 => sign = "+"
        else:
            temp = float((int(temp_high, 16) * 256 + int(temp_low, 16)))/10            
        battery = int(gh(data, 7)[0], 16) * 10  # percent
        rssi = int(gh(data, 7)[1], 16) * 100/16 # percent
 
        # send xPL
        self._callback("sensor.basic",
                       {"device" : address, 
                        "type" : "temp", 
                        "current" : temp, 
                        "units" : "c"})
        self._callback("sensor.basic",
                       {"device" : address, 
                        "type" : "battery", 
                        "current" : battery})
        self._callback("sensor.basic",
                       {"device" : address, 
                        "type" : "rssi", 
                        "current" : rssi})


    def _process_51(self, data):
        """ Humidity sensors

            !!! Not use actually !!!

            Type : sensor
            SDK version : 2.06
            Tested : No
        """
        pass        

        
    def _process_52(self, data):
        """ Temperature and humidity sensors
        
            Type : sensor
            SDK version : 2.06
            Tested : No
        """
        subtype = gh(data, 1)
        seqnbr = gh(data, 2)
        id = gh(data, 3,2)
        address = "th%s 0x%s" %(subtype[1], id)
        temp_high = gh(data, 5)
        temp_low = gh(data, 6)
        
        # first bit = 1 => sign = "-"
        if (int(temp_high, 16) & 0b1000000) == 0b10000000:
            temp = - float((int(temp_low, 16) + 256*(int(bin(temp_high, 16)) & 0b01111111)))/10
        # first bit = 0 => sign = "+"
        else:
            temp = float((int(temp_high, 16) * 256 + int(temp_low, 16)))/10
            
        humidity = int(gh(data, 7), 16) 
        humidity_status_code = ghexa(data, 8)
        humidity_status = HUMIDITY_STATUS[humidity_status_code]
        battery = int(gh(data, 9)[0], 16) * 10  # percent
        rssi = int(gh(data, 9)[1], 16) * 100/16 # percent
 
        # send xPL
        self._callback("sensor.basic",
                       {"device" : address, 
                        "type" : "temp", 
                        "current" : temp, 
                        "units" : "c"})
        self._callback("sensor.basic",
                       {"device" : address, 
                        "type" : "humidity", 
                        "current" : humidity, 
                        "description" : humidity_status})
        self._callback("sensor.basic",
                       {"device" : address, 
                        "type" : "status", 
                        "current" : humidity_status})
        self._callback("sensor.basic",
                       {"device" : address, 
                        "type" : "battery", 
                        "current" : battery})
        self._callback("sensor.basic",
                       {"device" : address, 
                        "type" : "rssi", 
                        "current" : rssi})

    
    def _process_53(self, data):
        """ Barometric sensors

            !!! Not use actually !!!

            Type : sensor
            SDK version : 2.06
            Tested : No
        """
        pass        

        
    def _process_54(self, data):
        """ Temperature, humidity and barometric sensors
        
            Type : sensor
            SDK version : 2.06
            Tested : No
        """
        subtype = gh(data, 1)
        seqnbr = gh(data, 2)
        id = gh(data, 3,2)
        address = "thb%s 0x%s" %(subtype[1], id)
        temp_high = gh(data, 5)
        temp_low = gh(data, 6)
        # first bit = 1 => sign = "-"
        if (int(temp_high, 16) & 0b1000000) == 0b10000000:
            temp = - float((int(temp_low, 16) + 256*(int(bin(temp_high, 16)) & 0b01111111)))/10
        # first bit = 0 => sign = "+"
        else:
            temp = float((int(temp_high, 16) * 256 + int(temp_low, 16)))/10
        humidity = int(gh(data, 7), 16) 
        humidity_status_code = ghexa(data, 8)
        humidity_status = HUMIDITY_STATUS[humidity_status_code]
        pressure = int(gh(data, 9, 2), 16)
        forecast_code = ghexa(data, 11)
        forecast = FORECAST[forecast_code]
        battery = int(gh(data, 12)[0], 16) * 10  # percent
        rssi = int(gh(data, 12)[1], 16) * 100/16 # percent
 
        # send xPL
        self._callback("sensor.basic",
                       {"device" : address, 
                        "type" : "temp", 
                        "current" : temp, 
                        "units" : "c"})
        self._callback("sensor.basic",
                       {"device" : address, 
                        "type" : "humidity", 
                        "current" : humidity})
        self._callback("sensor.basic",
                       {"device" : address, 
                        "type" : "pressure", 
                        "current" : pressure, 
                        "units" : "hpa", 
                        "forecast" : forecast})
        self._callback("sensor.basic",
                       {"device" : address, 
                        "type" : "battery", 
                        "current" : battery})
        self._callback("sensor.basic",
                       {"device" : address, 
                        "type" : "rssi", 
                        "current" : rssi})


    def _process_55(self, data):
        """ Rain sensors
        
            Type : sensor
            SDK version : 2.06
            Tested : No
        """
        subtype = gh(data, 1)
        seqnbr = gh(data, 2)
        id = gh(data, 3,2)
        address = "rain%s 0x%s" %(subtype[1], id)
        rain = int(gh(data, 5, 2), 16)
        if subtype == "02":
            rain = 100 * rain
        rain_total = int(gh(data, 7, 3), 16)
        battery = int(gh(data, 10)[0], 16) * 10  # percent
        rssi = int(gh(data, 10)[1], 16) * 100/16 # percent
 
        # send xPL
        self._callback("sensor.basic",
                       {"device" : address, 
                        "type" : "rainrate", 
                        "current" : rain, 
                        "units" : "mmh"})
        self._callback("sensor.basic",
                       {"device" : address, 
                        "type" : "raintotal", 
                        "current" : rain_total,  
                        "units" : "mm"})
        self._callback("sensor.basic",
                       {"device" : address, 
                        "type" : "battery", 
                        "current" : battery})
        self._callback("sensor.basic",
                       {"device" : address, 
                        "type" : "rssi", 
                        "current" : rssi})
    

    def _process_56(self, data):
        """ Wind sensors
        
            Type : sensor
            SDK version : 2.06
            Tested : No
        """
        subtype = gh(data, 1)
        seqnbr = gh(data, 2)
        id = gh(data, 3,2)
        address = "wind%s 0x%s" %(subtype[1], id)
        direction = int(gh(data, 5, 2), 16)
        av_speed = float(int(gh(data, 7, 2), 16)) / 10
        gust = float(int(gh(data, 9, 2), 16)) / 10
        battery = int(gh(data, 11)[0], 16) * 10  # percent
        rssi = int(gh(data, 11)[1], 16) * 100/16 # percent
 
        # send xPL
        self._callback("sensor.basic",
                       {"device" : address, 
                        "type" : "direction", 
                        "current" : direction})
        self._callback("sensor.basic",
                       {"device" : address, 
                        "type" : "gust", 
                        "current" : gust, 
                        "units" : "mps"})
        self._callback("sensor.basic",
                       {"device" : address, 
                        "type" : "average_speed", 
                        "current" : av_speed, 
                        "units" : "mps"})
        self._callback("sensor.basic",
                       {"device" : address, 
                        "type" : "battery", 
                        "current" : battery})
        self._callback("sensor.basic",
                       {"device" : address, 
                        "type" : "rssi", 
                        "current" : rssi})
    

    def _process_57(self, data):
        """ UV sensors
        
            Type : sensor
            SDK version : 2.06
            Tested : No
        """
        subtype = gh(data, 1)
        seqnbr = gh(data, 2)
        id = gh(data, 3,2)
        address = "uv%s 0x%s" %(subtype[1], id)
        uv = int(gh(data, 5, 1), 16)
        battery = int(gh(data, 6)[0], 16) * 10  # percent
        rssi = int(gh(data, 6)[1], 16) * 100/16 # percent
 
        # send xPL
        self._callback("sensor.basic",
                       {"device" : address, 
                        "type" : "uv", 
                        "current" : uv})
        self._callback("sensor.basic",
                       {"device" : address, 
                        "type" : "battery", 
                        "current" : battery})
        self._callback("sensor.basic",
                       {"device" : address, 
                        "type" : "rssi", 
                        "current" : rssi})
    

    def _process_58(self, data):
        """ Date/time sensors
            Type : sensor
            SDK version : n/a
            Tested : n/a
        """
        # warning : device RTGR328N send datetime to RFXCOM. There may be 
        # several datetime sent as several devices could be present.
        # Moreover, Domogik sends hour with its own xpl_time plugin. So,
        # in order not to SPAM xpl network with nothing useless, we don't
        # process datetime sensors ;)
        pass
    

    def _process_59(self, data):
        """ Current sensors
        
            Type : sensor
            SDK version : 2.06
            Tested : No
        """
        subtype = gh(data, 1)
        seqnbr = gh(data, 2)
        id = gh(data, 3,2)
        address = "elec1 0x%s" %(id)
        count = int(gh(data, 5, 1), 16)
        ch1 = float(int(gh(data, 6, 2), 16)) / 10
        ch2 = float(int(gh(data, 8, 2), 16)) / 10
        ch3 = float(int(gh(data, 10, 2), 16)) / 10
        battery = int(gh(data, 12)[0], 16) * 10  # percent
        rssi = int(gh(data, 12)[1], 16) * 100/16 # percent
 
        # send xPL
        self._callback("sensor.basic",
                       {"device" : address + "_1", 
                        "type" : "current", 
                        "current" : ch1})
        self._callback("sensor.basic",
                       {"device" : address + "_2", 
                        "type" : "current", 
                        "current" : ch2})
        self._callback("sensor.basic",
                       {"device" : address + "_3", 
                        "type" : "current", 
                        "current" : ch3})
        self._callback("sensor.basic",
                       {"device" : address, 
                        "type" : "battery", 
                        "current" : battery})
        self._callback("sensor.basic",
                       {"device" : address, 
                        "type" : "rssi", 
                        "current" : rssi})
    

    def _process_5a(self, data):
        """ Energieverbruik sensors
        
            Type : sensor
            SDK version : 2.06
            Tested : No
        """
        subtype = gh(data, 1)
        seqnbr = gh(data, 2)
        id = gh(data, 3,2)
        address = "elec2 0x%s" %(id)
        count = int(gh(data, 5, 1), 16)
        instant = float(int(gh(data, 6, 4), 16)) / 1000
        total = int(gh(data, 10, 6), 16)
        battery = int(gh(data, 16)[0], 16) * 10  # percent
        rssi = int(gh(data, 16)[1], 16) * 100/16 # percent
 
        # send xPL
        self._callback("sensor.basic",
                       {"device" : address, 
                        "type" : "power", 
                        "current" : instant, 
                        "units" : "kw"})
        self._callback("sensor.basic",
                       {"device" : address, 
                        "type" : "energy", 
                        "current" : total, 
                        "units" : "kwh"})
        self._callback("sensor.basic",
                       {"device" : address, 
                        "type" : "battery", 
                        "current" : battery})
        self._callback("sensor.basic",
                       {"device" : address, 
                        "type" : "rssi", 
                        "current" : rssi})
    

    ### 0x5B : Gas usage sensors
    # Reserved for futur use    
    

    ### 0x5C : Water usage sensors
    # Reserved for futur use    
    

    def _process_5d(self, data):
        """ Weighting scale
        
            Type : sensor
            SDK version : 2.06
            Tested : No
        """
        subtype = gh(data, 1)
        seqnbr = gh(data, 2)
        id = gh(data, 3,2)
        address = "weight%s 0x%s" %(subtype[1], id)
        weight = int(gh(data, 5, 2), 16)
        battery = int(gh(data, 7)[0], 16) * 10  # percent
        rssi = int(gh(data, 7)[1], 16) * 100/16 # percent
 
        # send xPL
        self._callback("sensor.basic",
                       {"device" : address, 
                        "type" : "weight", 
                        "current" : instant, 
                        "units" : "kg"})
        self._callback("sensor.basic",
                       {"device" : address, 
                        "type" : "battery", 
                        "current" : battery})
        self._callback("sensor.basic",
                       {"device" : address, 
                        "type" : "rssi", 
                        "current" : rssi})
    

    def _process_70(self, data):
        """ RFXsensor
        
            !!! Not produced anymore. Will me implemented only if needed !!!

            Type : sensor
            SDK version : 2.06
            Tested : No
        """
        pass        
    

    def _process_71(self, data):
        """ RFXMeter
        
            !!! Not produced anymore. Will me implemented only if needed !!!

            Type : sensor
            SDK version : 2.06
            Tested : No
        """
        pass        
    

    ### 0x80: I/O lines
    #TODO
    

    




def gh(data, num, len = 1):
    """ Get byte n° <num> from data to byte n° <num + len> in hexadecimal without 0x....
    """
    return data[num*2:(num+(len-1))*2+2]

def ghexa(data, num, len = 1):
    """ Get byte n° <num> from data to byte n° <num + len> in hexadecimal with 0x...
    """
    return "0x" + data[num*2:(num+(len-1))*2+2]

def gb(data, num):
    """ Get byte n° <num> from data to byte n° <num + len> in binary
    """
    return bin(int(data[num*2:(num)*2+2], 16))

def get_bit(bin_data, num, len = 1):
    """ Get bit n° <num> from bin data to bin n° <num + len>
        Return result in binary
    """
    num = num + 2 #in order to avoir "0b..."
    return '0b' + bin_data[num:(num+(len-1))+1]

def hexa(bin_data):
    """ Return hexadecimal value for bin data
        This is a shorcut function
    """
    return hex(int(bin_data, 2))
    
#def bin(s):
#    return str(s) if s<=1 else bin(s>>1) + str(s&1)
