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
  1 : {"id": "VMB8PB", "subtype": "INPUT"},
  2 : {"id": "VMB1RY", "subtype": "RELAY", "channels": 1},
  3 : {"id": "VMB1BL", "subtype": "BLIND", "channels": 1},
  5 : {"id": "VMB6IN", "subtype": "INPUT"},
  7 : {"id": "VMB1DM", "subtype": "DIMMER", "channels": 1},
  8 : {"id": "VMB4RY", "subtype": "RELAY", "channels": 4},
  9 : {"id": "VMB2BL", "subtype": "BLIND", "channels": 2},
 10 : {"id": "VMB8IR", "subtype": "INPUT"},
 11 : {"id": "VMB4PD", "subtype": "INPUT"},
 12 : {"id": "VMB1TS", "subtype": "TEMP"},
 13 : {"id": "VMB1TH", "subtype": "UNKNOWN"},
 14 : {"id": "VMB1TC", "subtype": "TEMP"},
 15 : {"id": "VMB1LED", "subtype": "DIMMER", "channels": 1},
 16 : {"id": "VMB4RYLD", "subtype": "RELAY", "channels": 4},
 17 : {"id": "VMB4RYNO", "subtype": "RELAY", "channels": 4},
 18 : {"id": "VMB4DC", "subtype": "DIMMER", "channels": 4},
 19 : {"id": "VMBMPD", "subtype": "UNKNOWN"},
 20 : {"id": "VMBDME", "subtype": "DIMMER", "channels": 1},
 21 : {"id": "VMBDMI", "subtype": "DIMMER", "channels": 1},
 22 : {"id": "VMB8PBU", "subtype": "INPUT"},
 23 : {"id": "VMB6PBN", "subtype": "INPUT"},
 24 : {"id": "VMB2PBN", "subtype": "INPUT"},
 25 : {"id": "VMB6PBB", "subtype": "INPUT"},
 26 : {"id": "VMB4RF", "subtype": "INPUT"},
 27 : {"id": "VMB1RYNO", "subtype": "RELAY", "channels": 1},
 28 : {"id": "VMB1BLE", "subtype": "UNKNOWN"},
 29 : {"id": "VMB2BLE", "subtype": "UNKNOWN"},
 30 : {"id": "VMBGP1", "subtype": "INPUT"},
 31 : {"id": "VMBGP2", "subtype": "INPUT"},
 32 : {"id": "VMBGP4", "subtype": "INPUT"},
 33 : {"id": "VMBGP0", "subtype": "INPUT"},
}

MSG_TYPES = {
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
        self._nodes = {}

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
       
    def scan(self):
        self._log.info("Starting the bus scan")
        for add in range(0,255):
            self.send_moduletyperequest(add)
        self._log.info("Bus scan finished")
 
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

    def send_level(self, address, channel, level):
        """ Set the level for a device
            if relay => level can only be 0 or 100
            if dimmer => level can be anything from 0 to 100
        """
        address = int(address)
        self._log.debug("received set_level for {0}".format(address))
        if address in self._nodes.keys():
            mtype = self._nodes[address] 
        else:
            self._log.error("Request to set a level on a device, but the device is not known. address {0}".format(address))
            return
        try:
            ltype = MODULE_TYPES[mtype]["subtype"]
        except KeyError:
            self._log.error("Request to set a level on a device, but the subtype is not known. mtype {0}".format(mtype))
            return
        if ltype == "DIMMER":
            """ Send dimemr value
            - speed = 1 second
            """
            level = (255 / 100) * level
            data = chr(0x07) + self._channels_to_byte(channel) + chr(int(level)) + chr(0x00) + chr(0x01)
            self.write_packet(address, data)
        elif int(level) == 255 and ltype == "RELAY":
            """ Send relay on message
            """
            data = chr(0x02) + self._channels_to_byte(channel)
            self.write_packet(address, data)
        elif int(level) == 0 and ltype == "RELAY":          
            """ Send relay off message
            """
            data = chr(0x01) + self._channels_to_byte(channel)
            self.write_packet(address, data)
        else:
            self._log.error("This methode should only be called for dimmers or relays and with level 0 to 255")
        return 
        
    def send_moduletyperequest(self, address):
        """ Request module type
        """
        self.write_packet(address, None)

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
            self._log.debug("start sending packet to {0}".format(hex(int(res["address"]))))
	    # start (8bit)
            packet = chr(0x0F)
            # priority (8bit, F8=high, FB=low)
            if res["data"] == None:
                packet += chr(0xFB)
            else:
                packet += chr(0xF8)
            # address (8bit)
            packet += chr(int(res["address"]))
            if res["data"] == None:
                # module type request
                packet += chr(0x40)
            else:
                packet += chr(len(res["data"]))
                # data
                packet += res["data"]
            # checksum (8bit)
            packet += self._checksum(packet)
            # end byte (8bit)
            packet += chr(0x04)
            self._log.debug( packet.encode('hex') )
	    # send
            if self._devtype == 'socket':
                self._dev.send( packet )
            else:
                self._dev.write( packet )
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
        try:
            __checksum = chr(__checksum)
        except ValueError:
            __checksum = chr(0) 
        return __checksum

    def _parser(self, data):
        """
           parse the velbus packet
        """
        assert isinstance(data, str)
        assert len(data) > 0
        assert len(data) >= 6
        assert ord(data[0]) == 0x0f
        self._log.debug("starting parser: %s" % data.encode('hex'))
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
        if data_size > 0:
            if ord(data[4]) in MSG_TYPES:
                # lookup the module type
                try:
                    if ord(data[2]) in self._nodes.keys():
                        mtype = self._nodes[ord(data[2])]
                    else:
                        mtype = None
                except KeyError:
                    mtype = None
                if mtype:
                    self._log.debug("Received message with type: '%s' address: %s module: %s(%s)" % (MSG_TYPES[ord(data[4])], ord(data[2]), MODULE_TYPES[mtype]['id'], mtype) )
                else:
                    self._log.debug("Received message with type: '%s' address: %s module: UNKNOWN" % (MSG_TYPES[ord(data[4])], ord(data[2])) )
                # first try the module specifick parser
                parsed = False
                if mtype:
                    try:
                        methodcall = getattr(self, "_process_{0}_{1}".format(ord(data[4]), mtype))
                        methodcall( data )
                        parsed = True
                    except AttributeError:
                        self._log.debug("Messagetype module specifick parser not implemented")	
                if not parsed:
                    try:
                        methodcall = getattr(self, "_process_{0}".format(ord(data[4])))
                        methodcall( data )
                    except AttributeError:
                        self._log.debug("Messagetype unimplemented {0}".format(ord(data[4])))
            else:
                self._log.warning("Received message with unknown type {0}".format(ord(data[4])))
        else:
            if (ord(data[3]) & 0x40 == 0x40):
                self._log.debug("Received module type request")			
            else:
                self._log.warning("zero sized message received without rtr set")

# procee the velbus received messages
# format will beL
#   _process_<messageId> => general parser for this messagetype
#   _process_<messageId>_<moduleType> => parser specifickly for this module type
    def _process_255(self, data):
        """
           Process a 255 Message
           Node type => send out as answer on a module_type_request
        """
        naddress = ord(data[2])
        ntype = ord(data[5])
        self._log.info("Found node with address {0} and module_type {1}".format(str(naddress), MODULE_TYPES[ntype]['id']))
        self._nodes[naddress] = ntype

    def _process_251_8(self, data):
        """
           Process a 251 Message
           Specifickly for VMB4RY
           Switch status => send out when a relay is switched
        """
        naddress = ord(data[2])
        #chan = self._blinchannel_to_byte(data[5])
        status = ord(data[7])
        
        #self._callback("lighting.device",
        #           {"device" : device,
        #            "level" : level})

    def _process_251(self, data):
        """
           Process a 251 Message
           Switch status => send out when a relay is switched
        """
        for channel in self._byte_to_channels(data[5]):
            address = str(ord(data[2]))
            channel = str(channel)
            level = -1
            if (ord(data[7]) & 0x03) == 0:
                level = 0
            if (ord(data[7]) & 0x03) == 1:
                level = 255
            if level != -1:
                self._callback("lighting.device",
                    {"device" : str(ord(data[2])),
                    "channel" : str(channel),
                    "level" : level})

    def _process_238(self, data):
        """
           Process a 251 Message
           Dimmer status => send out when the dimmer status is changed
        """
        level = -1
        level = (100 / 255 ) * ord(data[7])
        if level != -1:
            self._callback("lighting.device",
                {"device" : str(ord(data[2])),
                "channel": str(ord(data[5]) - 1),
                "level" : level})

    def _process_184(self, data):
        """
           Process a 184 Message
           Dimmer channel status => send out when the dimmer status is changed
        """
        for channel in self._byte_to_channels(data[5]):
            level = -1
            level = (100 / 255 ) * ord(data[7])
            if level != -1:
                self._callback("lighting.device",
                    {"device" : str(ord(data[2])),
                    "channel": str(channel),
                    "level" : level})
  
    def _process_0(self, data):
        """
           Process a 0 Message
           switch status => send out when an input (switch changed)
           HIGH = just pressed
           LOW = just released
           LONG = long pressed
        """
        device = str(ord(data[2]))
        chanpres = self._byte_to_channels(data[5])
        chanrel = self._byte_to_channels(data[6])
        chanlpres = self._byte_to_channels(data[7])
        for chan in chanpres:
            self._callback("sensor.basic",
               {"device": str(device), "channel": str(chan), "type": "input", "current": "HIGH" })
        for chan in chanlpres:
            self._callback("sensor.basic",
               {"device": str(device), "channel": str(chan), "type": "input", "current": "LONG" })
        for chan in chanrel:
            self._callback("sensor.basic",
               {"device": str(device), "channel": str(chan), "type": "input", "current": "LOW" })

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
	
    def _process_230(self, data):
        """
           Process a 230 message Temperature Sensor Temperature
           Databyte 2 => High byte current sensor temperature
           Databyte 3 => Low byte of current temperature sensor in two's complement format
           Resolution: 0.0625 degree celcius
        """
        device = str(ord(data[2]))
        cur = ord(data[5]) << 8
        cur = ((cur | ord(data[6])) / 32 ) * 0.0625
        low = ord(data[7]) << 8
        low = ((low | ord(data[8])) / 32 ) * 0.0625
        high = ord(data[9]) << 8
        high = ((high | ord(data[10])) / 32 ) * 0.0625
        self._callback("sensor.basic",
               {"device": device, "type": "temp", "units": "c",
               "current": str(cur), "lowest": str(low), "highest": str(high) })

# Some convert procs
    def _channels_to_byte(self, chan):
        """
           Convert a channel to a byte
           only works for one channel at a time
        """
        return chr( (1 << (int(chan) -1)) )

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


