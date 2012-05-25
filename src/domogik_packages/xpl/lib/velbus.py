# -*- coding: utf-8 -*-
"""
Velbus domogik plugin
"""

import serial
import socket
import traceback
import threading
from Queue import Queue

MODULE_TYPES = {
  1 : "VMB8PB",
  2 : "VMB1RY",
  3 : "VMB1BL",
  5 : "VMB6IN",
  7 : "VMB1DM",
  8 : "VMB4RY",
  9 : "VMB2BL",
 10 : "VMB8IR",
 11 : "VMB4PD",
 12 : "VMB1TS",
 13 : "VMB1TC",
 15 : "VMB1LED",
 16 : "VMB4RYLD",
 17 : "VMB4RYNO",
 18 : "VMB4DC",
 20 : "VMBDME",
 21 : "VMBDMI",
 22 : "VMB8PBU",
 23 : "VMB6PBN",
}

COMMAND_TYPES = {
  0 : "switch status",
  1 : "switch relay off",
  2 : "switch relay on",
  3 : "start relay timer",
  4 : "blind off",
  5 : "blind up",
  6 : "blind down",
  7 : "set dimmer value",
  8 : "start dimmer timer",
  9 : "bus off",
  10 : "bus active",
  11 : "rs232 buffer full",
  12 : "rs232 buffer empty",
  13 : "start blink relay timer",
  14 : "interface status request",
  15 : "slider status",
  96 : "firmware update request",
  97 : "firmware info",
  98 : "enter firmware upgrade",
  99 : "abort firmware upgrade",
  100 : "exit firmware upgrade",
  101 : "firmware upgrade started",
  102 : "write firmware memory",
  103 : "firmware memory",
  104 : "firmware memory write confirmed",
  105 : "read firmware memory",
  184 : "dimmer channel status",
  198 : "temperature settings part3",
  199 : "statistics request",
  200 : "statistics",
  201 : "read memory block",
  202 : "write memory block",
  203 : "memory dump request",
  204 : "memory block",
  205 : "lcd line text part1",
  206 : "lcd line text part2",
  207 : "lcd line text part3",
  208 : "lcd line text request",
  209 : "enable timer channels",
  210 : "reset backlight",
  211 : "reset pushbutton backlight",
  212 : "set pushbutton backlight",
  213 : "backlight status request",
  214 : "backlight",
  215 : "real time clock request",
  216 : "real time clock",
  217 : "error count request",
  218 : "error count",
  219 : "temperature sensor comfort mode",
  220 : "temperature sensor day mode",
  221 : "temperature sensor night mode",
  222 : "temperature sensor safe mode",
  223 : "temperature sensor cooling mode",
  224 : "temperature sensor heating mode",
  225 : "temperature sensor lock",
  226 : "temperature sensor unlock",
  227 : "set default sleep timer",
  228 : "temperature sensor set temperature",
  229 : "temperature sensor temperature request",
  230 : "temperature sensor temperature",
  231 : "temperature sensor request settings",
  232 : "temperature sensor settings part1",
  233 : "temperature sensor settings part2",
  234 : "temperature sensor status",
  235 : "IR reciever status",
  236 : "blind switch status",
  237 : "input switch status",
  238 : "dimmer status",
  239 : "module name request",
  240 : "module name part1",
  241 : "module name part2",
  242 : "module name part3",
  243 : "set backlight",
  244 : "update led status",
  245 : "clear led",
  246 : "set led",
  247 : "slow blinking led",
  248 : "fast blinking led",
  249 : "very fast blinking led",
  250 : "module status request",
  251 : "relay switch status",
  252 : "write eeprom data",
  253 : "read eeprom data",
  254 : "eeprom data status",
  255 : "node type",
}

class VelbusException(Exception):
    """
    Velbus exception
    """

    def __init__(self, value):
        Exception.__init__(self)
        self.value = value

    def __str__(self):
        return repr(self.value)


class VelbusDev:
    """
    Velbus domogik plugin
    """
    def __init__(self, log, cb_send_xpl, cb_send_trig, stop):
        """ Init object
            @param log : log instance
            @param cb_send_xpl : callback
            @param cb_send_trig : callback
            @param stop : 
        """
        self._log = log
        self._callback = cb_send_xpl
        self._cb_send_trig = cb_send_trig
        self._stop = stop
        self._dev = None
        self._devtype = 'serial'

        # Queue for writing packets to Rfxcom
        self.write_rfx = Queue()

        # Thread to process queue
        write_process = threading.Thread(None,
                                         self.write_daemon,
                                         "write_packets_process",
                                         (),
                                         {})
        write_process.start()

    def open(self, device, devicetype):
        """ Open (opens the device once)
	    @param device : the device string to open
        """
        self._devtype = devicetype
        try:
            self._log.info("Try to open VELBUS: %s" % device)
            if devicetype == 'socket':
                addr = device.split(':')
                addr = (addr[0], int(addr[1]))
                self._dev = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self._dev.connect( addr )
            else:
                self._dev = serial.Serial(device, 38400, timeout=0)
            self._log.info("VELBUS opened")
        except:
            error = "Error while opening Velbus : %s. Check if it is the good device or if you have the good permissions on it." % device
            raise VelbusException(error)

    def close(self):
        """ Close the open device
        """
        self._log.info("Close VELBUS")
        try:
            self._dev.close()
        except:
            error = "Error while closing device"
            raise VelbusException(error)
        
    def send_shutterup(self, address, channel):
        """ Send shutter up message
        """
        data = chr(0x05) + self._blinchannel_to_byte(channel) + chr(0x00) + chr(0x00) + chr(0x00)
        self.write_packet(address, data)
    
    def send_shutterdown(self, address, channel):
        """ Send shutter down message
        """
        data = chr(0x06) + self._blinchannel_to_byte(channel) + chr(0x00) + chr(0x00) + chr(0x00)
        self.write_packet(address, data)
    
    def send_relayon(self, address, channel):
        """ Send relay on message
        """
        data = chr(0x02) + self._channels_to_byte(channel)
        self.write_packet(address, data)
    
    def send_relayoff(self, address, channel):
        """ Send relay off message
        """
        data = chr(0x01) + self._channels_to_byte(channel)
        self.write_packet(address, data)

    def send_setdimmervalue(self, address, channel, level):
        """ Send dimemr value
            - speed = 1 second
        """
        data = chr(0x07) + self._channels_to_byte(channel) + chr(int(level)) + chr(0x00) + chr(0x01)
        self.write_packet(address, data)

    def send_moduletyperequest(self, address):
        """ Request module type
        """
        self.write_packet(address, chr(0x40))

    def write_packet(self, address, data):
        """ put a packet in the write queu
        """
        self._log.info("write packet")
        self.write_rfx.put_nowait( {"address": address,
					"data": data}) 

    def write_daemon(self):
        """ handle the queu
        """
        self._log.info("write deamon")
        while not self._stop.isSet():
            res = self.write_rfx.get(block = True)
            self._log.info("START SENDING PACKET TO %s" % hex(int(res["address"])))
	    # start
            packet = chr(0x0F)
            # priority
            packet += chr(0xF8)
            # address
            packet += chr(int(res["address"]))
            # rtr + datasize
            packet += chr(len(res["data"]))
            # data
            packet += res["data"]
            # checksum
            packet += self._checksum(packet)
            # end byte
            packet += chr(0x04)
            self._log.debug( packet.encode('hex') )
	    # send
            if self._devtype == 'socket':
                self._log.debug( self._dev.send( packet ) )
            else:
                self._log.debug( self._dev.write( packet ) )
            # sleep for 60ms
            self._stop.wait(0.06)
 
    def listen(self, stop):
        """ Listen thread for incomming VELBUS messages
        """
        self._log.info("Start listening VELBUS")
        # infinite
        try:
            while not stop.isSet():
                self.read()
        except:
            error = "Error while reading velbus device (disconnected ?) : %s" % traceback.format_exc()
            print(error)
            self._log.error(error)
            return

    def read(self):
        """ Read data from the velbus line
        """
        if self._devtype == 'socket':
            data = self._dev.recv(9999)
        else:
            data = self._dev.read(9999)
        if len(data) >= 6:
            if ord(data[0]) == 0x0f:
                size = ord(data[3]) & 0x0F
                self._parser(data[0:6+size])

    def _checksum(self, data):
        """
           Calculate the velbus checksum
        """
        assert isinstance(data, str)
        __checksum = 0
        for data_byte in data:
            __checksum += ord(data_byte)
        __checksum = -(__checksum % 256) + 256
        return chr(__checksum)

    def _parser(self, data):
        """
           parse the velbus packet
        """
        assert isinstance(data, str)
        assert len(data) > 0
        assert len(data) >= 6
        assert ord(data[0]) == 0x0f
        if len(data) > 14:
            self._log.warning("Velbus message: maximum %s bytes, this one is %s",
                str(14, str(len(data))))
            return
        if ord(data[-1]) != 0x04:
            self._log.warning("Velbus message: end byte not correct")
            return data
        if ord(data[1]) != 0xfb and ord(data[1]) != 0xf8:
            self._log.warning("Velbus message: unrecognized priority")
            return
        data_size = ord(data[3]) & 0x0F
        if data_size + 6 != len(data):
            self._log.warning("length of data size does not match actual length of message")
            return
        if not self._checksum(data[:-2]) == data[-2]:
            self._log.warning("Packet has no valid checksum")
            return
        if data_size >= 1:
            if ord(data[4]) in COMMAND_TYPES:
                self._log.debug("Received message with type: '%s' address: %s" % (COMMAND_TYPES[ord(data[4])], ord(data[2])) )
                try:
                    methodcall = getattr(self, "_process_" + str(ord(data[4])))
                    methodcall( data )
                except AttributeError:
                    self._log.debug("Messagetype unimplemented")		
            else:
                self._log.warning("Received message with unknown type %s" % ord(data[4]))
        else:
            if (ord(data[3]) & 0x40 == 0x40):
                self._log.debug("Received module type request")			
            else:
                self._log.warning("zero sized message received without rtr set")

# procee the velbus received messages
    def _process_251(self, data):
        """
           Process a 251 Message
           Switch status => send out when a relay is switched
        """
        for channel in self._byte_to_channels(data[5]):
            device = str(ord(data[2])) + "-" + str(channel)
            level = -1
            if (ord(data[7]) & 0x03) == 0:
                level = 0
            if (ord(data[7]) & 0x03) == 1:
                level = 255
            if level != -1:
                self._callback("lighting.device",
                    {"device" : device,
                    "level" : level})

    def _process_238(self, data):
        """
           Process a 251 Message
           Dimmer status => send out when the dimmer status is changed
        """
        device = str(ord(data[2])) + "-" + str(ord(data[5]) - 1)
        level = -1
        level = ord(data[7])
        if level != -1:
            self._callback("lighting.device",
                {"device" : device,
                "level" : level})

    def _process_184(self, data):
        """
           Process a 184 Message
           Dimmer channel status => send out when the dimmer status is changed
        """
        for channel in self._byte_to_channels(data[5]):
            device = str(ord(data[2])) + "-" + str(channel)
            level = -1
            level = ord(data[7])
            if level != -1:
                self._callback("lighting.device",
                    {"device" : device,
                    "level" : level})
  
    def _process_0(self, data):
        """
           Process a 0 Message
           switch status => send out when an input (switch changed)
        """
        chanPres = self._byte_to_channels(data[5])
        chanLPres = self._byte_to_channels(data[6])
        chanRel = self._byte_to_channels(data[7])
	self._log.debug("channels just pressed " + ''.join(map(str,chanPres)) )
	self._log.debug("channels long pressed " + ''.join(map(str,chanLPres)) )
	self._log.debug("channels just released " + ''.join(map(str,chanRel)) )

    def _process_236(self, data):
        """
           Process a 236 Message
           blind channel status => send out when the blind status changes
           chan <X> <status>
           chan: 00000011=1, 00001100=2
           status: 0=off, 1=chan 1 up, 2=chan 1 down, 4=chan 2 up, 8=chan 2 down

           foreach _byte_to_blindchannel(data[5])
		status _byte_to_channels data[7]                
        """
        chan = self._blinchannel_to_byte(data[5])
        device = str(ord(data[2]))
        status = self._byte_to_channels(data[7])
        command = []
        if chan == 1:
            if 1 in status:
                command = "up"
            if 2 in status:
                command = "down"
        elif chan == 2:
            if 4 in status:
                command = "up"
            if 8 in status:
                command = "down"
        else:
           command = "off"
        if command == "":
            self._callback("shutter.device",
               {"device" : device + "-" + chan,
               "command" : command})    
	
# Some convert procs
    def _channels_to_byte(self, chan):
        """
           Convert a channel to a byte
           only works for one channel at a time
        """
        return chr( (1 << (chan -1)) )

    def _byte_to_channels(self, byte):
        """
           Convert a byte to a channel list
        """
        assert isinstance(byte, str)
        assert len(byte) == 1
        byte = ord(byte)
        result = []
        for offset in range(0, 8):
            if byte & (1 << offset):
                result.append(offset+1)
        return result

    def _blinchannel_to_byte(self, channel):
        """
           Convert a channel 1 or 2 to its correct byte
        """
        assert isinstance(channel, int)
        if channel == 1:
            return chr(0x03)
        else:
            return chr(0x0C)

    def _byte_to_blindchannel(self, byte):
        """
           Convert a byte to its channel
        """
        if byte == chr(0x03):
            return 1
        else:
            return 2


