# -*- coding: utf-8 -*-

"""
This is a Python binding library for TellStick RF transciever.
It allows you to control several RF home automation device using
protocols on 433.92 Mhz band such as Chacon, HomeEasy, ...
It requires the telldus-core library is installed on your system.
Warning : The user you run your program under must :
- Have access to USB subsystem (for example on ubuntu your user
should be in the plugdev group.
- Have read AND write access to /etc/tellstick.conf file : this
is a requirement of the libtelldus-core C library
Example usage :
 ts = telldusAPI()
 ts.setOn("2")

For a list of supported protocols/models, please see the
telldus-core documentation :
 http://developer.telldus.se/wiki/TellStick_conf

References :
- Library telldus-core installation instructions :
 http://developer.telldus.se/wiki/TellStick_installation_Linux
- Telldus website (company building the TellStick and author
of the telldus-core C library)
 http://www.telldus.se

Thanks to :
Thibault Lamy <titi@poulpy.com> - http://www.poulpy.com
Julien Garet <julien@garet.info>
@author: Sebastien GALLET <sgallet@gmail.com>
@license: GPL(v3)
"""
from ctypes import cast
from ctypes import py_object
from ctypes import c_char_p
from ctypes import c_int
from ctypes import c_void_p
from ctypes import c_ubyte
from ctypes.util import find_library
import platform
import threading
from collections import deque
import traceback
from threading import Timer
from domogik.xpl.common.xplmessage import XplMessage
from pympler.asizeof import asizeof

#platform specific imports:
if (platform.system() == 'Windows'):
    #Windows
    from ctypes import windll, WINFUNCTYPE
else:
    #Linux
    from ctypes import cdll, CFUNCTYPE

# Device methods
TELLSTICK_TURNON = 1
TELLSTICK_TURNOFF = 2
TELLSTICK_BELL = 4
TELLSTICK_TOGGLE = 8
TELLSTICK_DIM = 16
TELLSTICK_LEARN = 32
TELLSTICK_EXECUTE = 64
TELLSTICK_UP = 128
TELLSTICK_DOWN = 256
TELLSTICK_STOP = 512
#Sensor value types
TELLSTICK_TEMPERATURE = 1
TELLSTICK_HUMIDITY = 2
#Error codes
TELLSTICK_SUCCESS = 0
TELLSTICK_ERROR_NOT_FOUND = -1
TELLSTICK_ERROR_PERMISSION_DENIED = -2
TELLSTICK_ERROR_DEVICE_NOT_FOUND = -3
TELLSTICK_ERROR_METHOD_NOT_SUPPORTED = -4
TELLSTICK_ERROR_COMMUNICATION = -5
TELLSTICK_ERROR_CONNECTING_SERVICE = -6
TELLSTICK_ERROR_UNKNOWN_RESPONSE = -7
TELLSTICK_ERROR_UNKNOWN = -99
#Device typedef
TELLSTICK_TYPE_DEVICE = 1
TELLSTICK_TYPE_GROUP = 2
TELLSTICK_TYPE_SCENE = 3
#Device changes
TELLSTICK_DEVICE_ADDED = 1
TELLSTICK_DEVICE_CHANGED = 2
TELLSTICK_DEVICE_REMOVED = 3
TELLSTICK_DEVICE_STATE_CHANGED = 4
#Change types
TELLSTICK_CHANGE_NAME = 1
TELLSTICK_CHANGE_PROTOCOL = 2
TELLSTICK_CHANGE_MODEL = 3
TELLSTICK_CHANGE_METHOD = 4

# Device methods
TELLDUS_BRIGHT = 3
TELLDUS_SHINE = 5
TELLDUS_CHANGE = 7
TELLDUS_SHUT = 201

#DEVICETYPES
TELLDUS_LIGHTING = "lighting"
TELLDUS_SHUTTER = "shutter"
TELLDUS_SENSOR = "sensor"
TELLDUS_DAWNDUSK = "dawndusk"

#MEMORY USAGE
MEMORY_PLUGIN = 1
MEMORY_API = 2
MEMORY_CONFIG = 3
MEMORY_DEVICE_QUEUE = 4
MEMORY_FIFO = 5
MEMORY_RTIMER = 6
MEMORY_STIMER = 7
MEMORY_ACK = 8
MEMORY_LAST = 9

DEVICEEVENTLOCK = threading.Lock()
QUEUELOCK = threading.Lock()

MULTI_SHUTTER_DOWN = 1.2
MULTI_SHUTTER_UP = 1.5

#def sensor_event_callback(protocol, model, deviceid, datatype, \
#    '''
#    Add Device to the dictionnary
#    '''
#    value, timestamp, callbackid, context):
#    print "sensorEventCallback: id=%s, method=%s and data=%s" % \
#        (deviceid, model, value)

def device_event_callback(deviceid, method, value, callbackid, context):
    '''
    Callback procedure when a device event income.
    '''
    if deviceid == 0 or method == 0 :
        return
    obj = cast(context, py_object).value
    #print "deviceEventCallback: id=%s, method=%s and value=%s" % (deviceid, method, value)
    obj.receive(deviceid, method, c_char_p(value).value, callbackid)

def device_change_event_callback(deviceid, changeevent,
    changetype, callbackid, context):
    '''
    Callback procedure when a device change event income.
    '''
    obj = cast(context, py_object).value
    obj.log.debug("deviceChangeEventCallback: id=%s, changeEvent=%s and \
        changeType=%s" % (deviceid, changeevent, changetype))

class TelldusException(Exception):
    """
    telldus exception
    """
    def __init__(self, value):
        '''
        Add Device to the dictionnary
        '''
        Exception.__init__(self)
        self.value = value

    def __str__(self):
        '''
        Add Device to the dictionnary
        '''
        return repr(self.value)

class TelldusAPI:
    '''
    Telldus plugin library
    '''
    def __init__(self, send_xpl_cmd, log, config):
        '''
        Constructor : Find telldus-core library and try to open it
        If success : initialize telldus API
        @param xplCallback : method of the plug in to send xpl messages
        @param log : a logger
        @param config : the plugin configurator to use. None to disable
        the receiver.
        '''
        self.log = log
        self.log.info("telldusAPI.__init__ : Start ...")
        self.config = config
        self._send_xpl_cmd = send_xpl_cmd
        self._config = {}
        #The delay to filter incoming messages from telldus
        self._delayrf = 0.4
        #The delay to use when sending batch messages
        self._delaybatch = self._delayrf * 5
        #The maximun batch items to create
        self._maxbatch = 10
        self._deviceeventq = None
        self.log.info("telldusAPI.__init__ : Look for telldus-core")
        # Initialize tellDus API
        try:
            self._telldusd = Telldusd()
        except:
            self.log.error("Error loading telldusd : %s" % (traceback.format_exc()))
        try:
            self.helpers = Helpers(self._telldusd)
        except:
            self.log.error("Error loading helpers : %s" % (traceback.format_exc()))
        self.reload_config()
        self.log.debug("telldusAPI.__init__ : Done :-)")

    def reload_config(self):
        '''
        Load devices into the _devices dictionnary
        '''
        self.log.debug("reload_config : Start")
        try:
            delay = float(self.config.query('telldus', 'delayrf'))
            self._delayrf = delay
            self._delaybatch = self._delayrf * 5
        except:
            self.log.warning("Can't get delay RF configuration from XPL. Use default one.")
        try:
            self._deviceeventq = DeviceEventQueue(self, self._delayrf, self._telldusd)
        except:
            self.log.error("Error creating the device event queue : %s" % \
                     (traceback.format_exc()))
        self._config = {}
        num = 1
        loop = True
        while loop == True:
            name = self.config.query('telldus', 'name-%s' % str(num))
            devicetype = self.config.query('telldus',
                'devicetype-%s' % str(num))
            param1 = self.config.query('telldus', 'param1-%s' % str(num))
            param2 = self.config.query('telldus', 'param2-%s' % str(num))
            if name != None:
                self._config[name] = {"devicetype" : devicetype,
                    "param1" : param1, "param2" : param2}
            else:
                loop = False
            num += 1
        self.log.debug("reload_config : Done :-)")

    def memory_usage(self, which):
        '''
        Return the memory used by an object
        '''
        self.log.debug("memory_usage : Start")
        if which == 0 :
            print "Memory usage :"
            print "api : %s octets" % asizeof(self)
            print "config : %s octets" % asizeof(self._config)
            print "device queue : %s octets" % self._deviceeventq.memory_usage(MEMORY_DEVICE_QUEUE)
            print "fifo : %s octets" % self._deviceeventq.memory_usage(MEMORY_FIFO)
            print "received timers : %s octets" % self._deviceeventq.memory_usage(MEMORY_RTIMER)
            print "sent timers : %s octets" % self._deviceeventq.memory_usage(MEMORY_STIMER)
            print "ACKs to send : %s octets" % self._deviceeventq.memory_usage(MEMORY_ACK)
            print "last commands sent : %s octets" % self._deviceeventq.memory_usage(MEMORY_LAST)
        else:
            if which == MEMORY_PLUGIN:
                return 0
            elif which == MEMORY_API:
                return asizeof(self)
            elif which == MEMORY_CONFIG:
                return asizeof(self._config)
            elif which == MEMORY_DEVICE_QUEUE:
                return self._deviceeventq.memory_usage(MEMORY_DEVICE_QUEUE)
            elif which == MEMORY_FIFO:
                return self._deviceeventq.memory_usage(MEMORY_FIFO)
            elif which == MEMORY_RTIMER:
                return self._deviceeventq.memory_usage(MEMORY_RTIMER)
            elif which == MEMORY_STIMER:
                return self._deviceeventq.memory_usage(MEMORY_STIMER)
            elif which == MEMORY_ACK:
                return self._deviceeventq.memory_usage(MEMORY_ACK)
            elif which == MEMORY_LAST:
                return self._deviceeventq.memory_usage(MEMORY_LAST)
        self.log.debug("memory_usage : Done :-)")

    def send_xpl(self, xpltype, deviceid, method, value):
        """
        Send an xpl message : ie an xpl-trig
        @param deviceid : the id of the device
        @param method : the method
        @param value : the value
        """
        self.log.debug("send_xpl : Start ...")
        if self.get_device(deviceid) in self._config:
            devicetype = self._config[self.get_device(deviceid)]['devicetype']
            if devicetype == TELLDUS_SENSOR :
                self.send_xpl_sensor_basic("xpl-trig", deviceid, method, value)
                #self.send_xpl_telldus_basic(xpltype, deviceid, method, value)
            elif devicetype == TELLDUS_DAWNDUSK :
                self.log.info("TELLDUS_DAWNDUSK : Not implemented")
                self.send_xpl_telldus_basic(xpltype, deviceid, method, value)
            elif devicetype == TELLDUS_LIGHTING :
                self.log.info("TELLDUS_LIGHTING : Not implemented")
                self.send_xpl_telldus_basic(xpltype, deviceid, method, value)
            elif devicetype == TELLDUS_SHUTTER :
                self.log.info("TELLDUS_SHUTTER : Not implemented")
                self.send_xpl_telldus_basic(xpltype, deviceid, method, value)
        else :
            self.send_xpl_telldus_basic(xpltype, deviceid, method, value)
        self.log.debug("send_xpl : Done")

    def send_xpl_telldus_basic(self, xpltype, deviceid, method, value):
        """
        Send an xpl message : ie an xpl-trig
        @param deviceid : the id of the device
        @param method : the method
        @param value : the value
        """
        mess = XplMessage()
        mess.set_type(xpltype)
        mess.set_schema("telldus.basic")
        mess.add_data({"device" :  self._telldusd.get_device(deviceid)})
        mess.add_data({"command" :  self._telldusd.xplcommands[method]["cmd"]})
        if value:
            mess.add_data({"level" : value})
        elif self._telldusd.xplcommands[method]["cmd"] == \
          self._telldusd.xplcommands[TELLSTICK_DIM]["cmd"] :
            mess.add_data({"level" : value})
        elif self._telldusd.xplcommands[method]["cmd"] == \
          self._telldusd.xplcommands[TELLDUS_BRIGHT]["cmd"] :
            mess.add_data({"level" : value})
        elif self._telldusd.xplcommands[method]["cmd"] == \
          self._telldusd.xplcommands[TELLDUS_SHINE]["cmd"] :
            mess.add_data({"level" : value})
        elif self._telldusd.xplcommands[method]["cmd"] == \
          self._telldusd.xplcommands[TELLDUS_SHUT]["cmd"] :
            mess.add_data({"level" : value})
        elif self._telldusd.xplcommands[method]["cmd"] == \
          self._telldusd.xplcommands[TELLDUS_CHANGE]["cmd"] :
            mess.add_data({"level" : value})
        self._send_xpl_cmd(mess)

    def send_xpl_sensor_basic(self, xpltype, deviceid, method, value):
        """
        Send an xpl message : ie an xpl-trig
        @param deviceid : the id of the device
        @param method : the method
        @param value : the value
        """
        mess = XplMessage()
        mess.set_type("xpl-trig")
        mess.set_schema("sensor.basic")
        mess.add_data({"device" :  self._telldusd.get_device(deviceid)})
        mess.add_data({"type" :  "telldus"})
        if method == TELLSTICK_TURNON :
            mess.add_data({"current" : "high"})
        elif method == TELLSTICK_TURNOFF :
            mess.add_data({"current" : "low"})
        self._send_xpl_cmd(mess)

    def send_xpl_ack(self, deviceid, method, value):
        """
        Send an ack xpl message : ie an xpl-trig
        @param deviceid : the id of the device
        @param method : the method
        @param value : the value
        """
        self.log.debug("send_xpl_ack : Start ...")
        self.send_xpl("xpl-trig", deviceid, method, value)
        self.log.debug("send_xpl_ack : Done")

    def send_xpl_new(self, deviceid, method, value):
        """
        Send a new xpl message : ie an xpl-cmnd for lighting controllers
        or xpl-trig for sensors
        @param deviceid : the id of the device
        @param method : the method
        @param value : the value
        """
        self.log.debug("send_xpl_new : Start ...")
        self.send_xpl("xpl-cmnd", deviceid, method, value)
        self.log.debug("send_xpl_new : Done")

    def get_device_id(self, device):
        '''
        Retrieve an id from HU address
        @param device : address of the module (ie TS14)
        @return : Id of the device (14)
        '''
        return self._telldusd.get_device_id(device)

    def get_device(self, deviceid):
        '''
        Retrieve an address device from deviceid
        @param deviceid : id of the device (ie 14)
        @return : address of the device (ie TS14)
        '''
        return self._telldusd.get_device(deviceid)

    def lighting_activate_device(self, device, channel, level, faderate):
        '''
        Activate a device during a scene process.
        @param device : address of the device (ie TS14)
        @param channel : Not used in this case
        @param level : level of light. 0 to say OFF and 100 to say ON
        @param faderate : the duration of the scene
        '''
        level = int(level)
        faderate = int(faderate)
        if level == 0 :
            self.send_off(device)
        elif level > 100 :
            self.send_on(device)
        else :
            if faderate == 0:
                self.send_dim(device, level)
            else :
                self.send_change(device, level, faderate)

    def lighting_deactivate_device(self, device, channel, level, faderate):
        '''
        Deactivate a device during a scene process.
        @param device : address of the device (ie TS14)
        @param channel : Not used in this case
        @param level : level of light. 0 to say OFF and 100 to say ON
        @param faderate : the duration of the scene
        '''
        self.send_off(device)

    def lighting_valid_device(self, device, channel):
        '''
        Check that device is managed by this plugin. Called when the scene
        configuration is loaded.
        The first way to do ti is to check the device syntax.
        We only accept device like TSX, where X is an integer.
        In this case, we do not check that this device exists on telldusd.
        The second way to do it, is to try to get configuration from telldusd.
        @param deviceid : id of the device (ie 14)
        @return : address of the device (ie TS14)
        '''
        return self._telldusd.check_device(device)

    def send_on(self, device):
        '''
        Turns the specified device On
        @param device : address of the device (ie TS14)
        '''
        #print " ON : address: %s" % (add)
        self._deviceeventq.send_command(self.get_device_id(device),
                                        TELLSTICK_TURNON, 0)

    def send_off(self, device):
        '''
        Turns the specified device Off
        @param add : address of the module (ie TS14)
        '''
        #print " OFF : address: %s" % (add)
        self._deviceeventq.send_command(self.get_device_id(device),
                                        TELLSTICK_TURNOFF, 0)

    def send_dim(self, device, level):
        '''
        Sets the specified dim level on device
        Level should be between 0 and 100
        @param add : address of the module (ie
        TS14)
        @param level : level of light (0..100)
        '''
        #print "dim level=%s"%type(level)
        if level == None or level == "None":
            level = "0"
        level = int(level)
        #telldus wait a level from 0 to 255
        #but xpl use a value from 0 to 100
        tdlevel = int(level * 2.55)
        deviceid = self.get_device_id(device)
        if tdlevel <= 0:
            self._deviceeventq.create_batch(deviceid, TELLSTICK_DIM, 0)
            self._deviceeventq.add_batch(deviceid, TELLSTICK_TURNOFF, 0, 0)
            self._deviceeventq.start_batch(deviceid)
        elif tdlevel >= 255:
            self._deviceeventq.create_batch(deviceid, TELLSTICK_DIM, 100)
            self._deviceeventq.add_batch(deviceid, TELLSTICK_TURNON, 0, 0)
            self._deviceeventq.start_batch(deviceid)
        else :
            self._deviceeventq.create_batch(deviceid, TELLSTICK_DIM, level)
            self._deviceeventq.add_batch(deviceid, TELLSTICK_DIM, tdlevel, 0)
            self._deviceeventq.start_batch(deviceid)

    def send_bright(self, device, level, faderate):
        '''
        Turn on the device and after set the specified dim level on device
        Level should be between 0 and 255
        @param add : address of the module (ie TS14)
        @param level : level of light (0..255max)
        @param faderate : duration in seconds of th shine process
        '''
        #print " BRIGHT : address: %s, level: %s" % (device, level)
        if level == None or level == "None":
            level = "0"
        level = int(level)
        if faderate == None or faderate == "None":
            faderate = "0"
        faderate = int(faderate)
        #faderate = 20
        tdlevel = level * 2.55
        steps = faderate / self._delaybatch
        if steps > self._maxbatch:
            steps = self._maxbatch
        deviceid = self.get_device_id(device)
        if tdlevel <= 0:
            self._deviceeventq.create_batch(deviceid, TELLDUS_BRIGHT, 0)
            if faderate == 0:
                self._deviceeventq.add_batch(deviceid, TELLSTICK_TURNOFF, 0, faderate)
            else:
                self._deviceeventq.add_batch(deviceid, TELLSTICK_TURNON, 0, 0)
                self._deviceeventq.add_batch(deviceid, TELLSTICK_TURNOFF, 0, faderate)
            self._deviceeventq.start_batch(deviceid)
        elif tdlevel >= 255:
            self._deviceeventq.create_batch(deviceid, TELLDUS_BRIGHT, 100)
            self._deviceeventq.add_batch(deviceid, TELLSTICK_TURNON, 0, 0)
            self._deviceeventq.start_batch(deviceid)
        else :
            if faderate == 0:
                self._deviceeventq.create_batch(deviceid, TELLDUS_BRIGHT, level)
                self._deviceeventq.add_batch(deviceid, TELLSTICK_TURNON, 0, 0)
                self._deviceeventq.add_batch(deviceid, TELLSTICK_DIM, tdlevel, faderate)
                self._deviceeventq.start_batch(deviceid)
            else:
                self._deviceeventq.create_batch(deviceid, TELLDUS_BRIGHT, level)
                step = (255-tdlevel) / steps
                delay = faderate / steps
                #print "faderate=%s, steps=%s, dimstep=%s" % (faderate, steps, step)
                for i in range(0, int(steps)):
                    #print "i=%s" % i
                    self._deviceeventq.add_batch(deviceid, TELLSTICK_DIM, int(255-i*step), int(i*delay))
                self._deviceeventq.add_batch(deviceid, TELLSTICK_DIM, tdlevel, faderate)
                self._deviceeventq.start_batch(deviceid)

    def send_shine(self, device, level, faderate):
        '''
        Turn on the device gradually up to level during faderate seconds
        @param add : address of the module (ie TS14)
        @param level : level of light (0..255max)
        @param faderate : duration in seconds of th shine process
        '''
        #print " SHINE : address: %s, level: %s" % (device, level)
        if level == None or level == "None":
            level = "0"
        level = int(level)
        if faderate == None or faderate == "None":
            faderate = "0"
        faderate = int(faderate)
        #faderate = 20
        tdlevel = level * 2.55
        steps = faderate / self._delaybatch
        if steps > self._maxbatch:
            steps = self._maxbatch
        deviceid = self.get_device_id(device)
        if tdlevel <= 0:
            self._deviceeventq.create_batch(deviceid, TELLDUS_SHINE, 0)
            self._deviceeventq.add_batch(deviceid, TELLSTICK_TURNOFF, 0, 0)
            self._deviceeventq.start_batch(deviceid)
        else :
            if tdlevel >= 255:
                tdlevel = 255
            if faderate == 0:
                self._deviceeventq.create_batch(deviceid, TELLDUS_SHINE, level)
                self._deviceeventq.add_batch(deviceid, TELLSTICK_DIM, tdlevel, faderate)
                self._deviceeventq.start_batch(deviceid)
            else:
                self._deviceeventq.create_batch(deviceid, TELLDUS_SHINE, level)
                step = tdlevel / steps
                delay = faderate / steps
                #print "faderate=%s, steps=%s, dimstep=%s, delay=%s" % (faderate, steps, step, delay)
                for i in range(0, int(steps)):
                    #print "i=%s" % i
                    self._deviceeventq.add_batch(deviceid, TELLSTICK_DIM, int(i*step), int(i*delay))
                self._deviceeventq.add_batch(deviceid, TELLSTICK_DIM, tdlevel, faderate)
                self._deviceeventq.start_batch(deviceid)

    def send_change(self, device, level, faderate):
        '''
        Change the current light gradually, using the previous value saved in
        lastent as start value.
        @param add : address of the module (ie TS14)
        @param level : level of light (0..255max)
        @param faderate : duration in seconds of th shine process
        '''
        #print " SHINE : address: %s, level: %s" % (device, level)
        deviceid = self.get_device_id(device)
        old = self._deviceeventq.get_last_sent(deviceid)
        downtime = 15
        if device in self._config:
            devicetype = self._config[device]['devicetype']
            if devicetype == TELLDUS_SHUTTER:
                downtime = float(self._config[device]['param1'])
#        print "old %s = %s" % (deviceid,old)
        if level == None or level == "None":
            level = "0"
        level = int(level)
        if faderate == None or faderate == "None":
            faderate = "0"
        faderate = int(faderate)
        #faderate = 20
        start = 0
        if old == None:
            start = 0
        elif old["method"] == TELLSTICK_TURNON:
            start = 100
        else:
            start = int(old["value"])
        print " start = %s" % start
        tdlevel = level * 2.55
        tdstart = start * 2.55
        steps = faderate / self._delaybatch
        if steps > self._maxbatch:
            steps = self._maxbatch
        deviceid = self.get_device_id(device)
        if tdlevel <= 0:
            tdlevel = 0
        elif tdlevel >= 255:
            tdlevel = 255
        if faderate == 0:
            self._deviceeventq.create_batch(deviceid, TELLDUS_CHANGE, level)
            self._deviceeventq.add_batch(deviceid, TELLSTICK_DIM, tdlevel, faderate)
            self._deviceeventq.start_batch(deviceid)
        else:
            self._deviceeventq.create_batch(deviceid, TELLDUS_CHANGE, level)
            step = (tdlevel - start) / steps
            delay = faderate / steps
            #print "faderate=%s, steps=%s, dimstep=%s, delay=%s" % (faderate, steps, step, delay)
            for i in range(0, int(steps)):
                #print "i=%s" % i
                self._deviceeventq.add_batch(deviceid, TELLSTICK_DIM, int(start + i*step), int(i*delay))
            self._deviceeventq.add_batch(deviceid, TELLSTICK_DIM, tdlevel, faderate)
            self._deviceeventq.start_batch(deviceid)

    def send_bell(self, device):
        '''
        Sends the bell signal to device
        @param add : address of the module (ie TS14)
        '''
        self._deviceeventq.send_command(self.get_device_id(device),
                                TELLSTICK_BELL, 0)

    def send_up(self, device):
        '''
        Move the shutter up.
        @param add : address of the module (ie TS14)
        '''
        #print " up : address: %s" % (device)
        deviceid = self.get_device_id(device)
        downtime = 15
        if device in self._config:
            devicetype = self._config[device]['devicetype']
            if devicetype == TELLDUS_SHUTTER:
                downtime = float(self._config[device]['param1'])
        if self._telldusd.methods(deviceid, TELLSTICK_UP) == TELLSTICK_UP:
            self._deviceeventq.send_command(deviceid, TELLSTICK_UP, 0)
        elif self._telldusd.methods(deviceid, TELLSTICK_TURNON) == TELLSTICK_TURNON:
            self._deviceeventq.create_batch(deviceid, TELLSTICK_UP, 0)
            self._deviceeventq.add_batch(deviceid, TELLSTICK_TURNON, 0, 0)
            #self._deviceeventq.add_batch(deviceid, TELLSTICK_TURNON, 0, downtime*MULTI_SHUTTER_UP)
            self._deviceeventq.start_batch(deviceid)

    def send_down(self, device):
        '''
        Move the shutter down.
        @param add : address of the module (ie TS14)
        '''
        #print " down : address: %s" % (device)
        deviceid = self.get_device_id(device)
        downtime = 15
        if device in self._config:
            devicetype = self._config[device]['devicetype']
            if devicetype == TELLDUS_SHUTTER:
                downtime = float(self._config[device]['param1'])
        if self._telldusd.methods(deviceid, TELLSTICK_DOWN) == TELLSTICK_DOWN:
            self._deviceeventq.send_command(deviceid, TELLSTICK_DOWN, 0)
        elif self._telldusd.methods(deviceid, TELLSTICK_TURNOFF) == TELLSTICK_TURNOFF:
            self._deviceeventq.create_batch(deviceid, TELLSTICK_DOWN, 0)
            self._deviceeventq.add_batch(deviceid, TELLSTICK_TURNOFF, 0, 0)
            #self._deviceeventq.add_batch(deviceid, TELLSTICK_TURNOFF, 0, downtime*MULTI_SHUTTER_DOWN)
            self._deviceeventq.start_batch(deviceid)

    def send_shut(self, device, level):
        '''
        Open the shutter depending on level
        Level should be between 0 and 4
        @param add : address of the module (ie TS14)
        @param level : level of light (0..255max)
        '''
        #print " SHUT : address: %s, level: %s" % (device, level)
        deviceid = self.get_device_id(device)
        downtime = 15
        if device in self._config:
            devicetype = self._config[device]['devicetype']
            if devicetype == TELLDUS_SHUTTER:
                downtime = float(self._config[device]['param1'])
        if level == 0 :
            if self._telldusd.methods(deviceid, TELLSTICK_DOWN) == TELLSTICK_DOWN:
                self._deviceeventq.send_command(deviceid, TELLSTICK_DOWN, 0)
            elif self._telldusd.methods(deviceid, TELLSTICK_TURNOFF) == TELLSTICK_TURNOFF:
                self._deviceeventq.create_batch(deviceid, TELLSTICK_DOWN, 0)
                self._deviceeventq.add_batch(deviceid, TELLSTICK_TURNOFF, 0, 0)
                #self._deviceeventq.add_batch(deviceid, TELLSTICK_TURNOFF, 0, downtime*MULTI_SHUTTER_DOWN)
                self._deviceeventq.start_batch(deviceid)
        elif level == 100 :
            if self._telldusd.methods(deviceid, TELLSTICK_UP) == TELLSTICK_UP:
                self._deviceeventq.send_command(deviceid, TELLSTICK_UP, 0)
            elif self._telldusd.methods(deviceid, TELLSTICK_TURNON) == TELLSTICK_TURNON:
                self._deviceeventq.create_batch(deviceid, TELLSTICK_UP, 0)
                self._deviceeventq.add_batch(deviceid, TELLSTICK_TURNON, 0, 0)
                #self._deviceeventq.add_batch(deviceid, TELLSTICK_TURNON, 0, downtime*MULTI_SHUTTER_UP)
                self._deviceeventq.start_batch(deviceid)
        else :
            level = int(level)
            if self._telldusd.methods(deviceid, TELLSTICK_UP) == TELLSTICK_UP:
                self._deviceeventq.create_batch(deviceid, TELLDUS_SHUT, level)
                self._deviceeventq.add_batch(deviceid, TELLSTICK_UP, 0, 0)
                self._deviceeventq.add_batch(deviceid, TELLSTICK_DOWN, 0, downtime*MULTI_SHUTTER_UP)
                self._deviceeventq.add_batch(deviceid, TELLSTICK_STOP, 0, downtime*MULTI_SHUTTER_UP+downtime*(1.0-level/100.0))
                self._deviceeventq.start_batch(deviceid)
            elif self._telldusd.methods(deviceid, TELLSTICK_TURNON) == TELLSTICK_TURNON:
                self._deviceeventq.create_batch(deviceid, TELLDUS_SHUT, level)
                self._deviceeventq.add_batch(deviceid, TELLSTICK_TURNON, 0, 0)
                self._deviceeventq.add_batch(deviceid, TELLSTICK_TURNOFF, 0, downtime*MULTI_SHUTTER_UP)
                self._deviceeventq.add_batch(deviceid, TELLSTICK_TURNOFF, 0, downtime*MULTI_SHUTTER_UP+downtime*(1.0-level/100.0))
                self._deviceeventq.start_batch(deviceid)

    def send_stop(self, device):
        '''
        Stop the shutter.
        @param add : address of the module (ie TS14)
        '''
        #print " stop : address: %s" % (device)
        deviceid = self.get_device_id(device)
        if self._telldusd.methods(deviceid, TELLSTICK_STOP) == TELLSTICK_STOP:
            self._deviceeventq.send_command(deviceid, TELLSTICK_STOP, 0)
        elif self._telldusd.methods(deviceid, TELLSTICK_TURNOFF) == TELLSTICK_TURNOFF:
            self._deviceeventq.resend_command(deviceid, TELLSTICK_STOP, 0, active_batch = True)

class DeviceEventQueue:
    '''
    This class is the interface to the tellsticK.
    It sends commands and wait for ack.
    It can also send complex command via batch jobs.
    @param parent : the library used to sent the xpl message
    @param delay_rf : the delay to filter RF messages
    @param telldusd : the "daemon" used to communicate with the tellstick
    '''
    def __init__(self, parent, delayrf, telldusd):
        '''
        Init the class
        '''
        self._delayrf = delayrf
        self._telldusd = telldusd
        self._parent = parent
        #The timers used to filter the incoming RF commands.
        self._received_timers = dict()
        self._refused_timers = dict()
        #The timers used to send the batch jobs.
        self._sent_timers = dict()
        #The fifos used to store.
        self._fifos = dict()
        #The last command sent to the tellstick. Does not contains the
        #batch master command
        self._lastsents = dict()
        #The trig message to send when the cycle is complete.
        self._ackstosend = dict()
        #Register the device event procedure.
        self._telldusd.register_device_event(self)

    def __del__(self):
        '''
        Destroy the class
        '''
        if self._telldusd:
            self._telldusd.unregister_device_event()
        #print "DeviceEventQueue.__del__ is called"


    def memory_usage(self, which):
        '''
        Return the memory used by an object
        '''
        if which == MEMORY_DEVICE_QUEUE:
            return asizeof(self)
        elif which == MEMORY_FIFO:
            return asizeof(self._fifos)
        elif which == MEMORY_RTIMER:
            #print "self._received_timers : %s" % self._received_timers
            #print "self._refused_timers : %s" % self._refused_timers
            return asizeof(self._received_timers) + asizeof(self._refused_timers)
        elif which == MEMORY_STIMER:
            return asizeof(self._sent_timers)
        elif which == MEMORY_ACK:
            return asizeof(self._ackstosend)
        elif which == MEMORY_LAST:
            return asizeof(self._lastsents)
        else :
            return 0

    def _clean_batch(self, deviceid):
        '''
        Clear the batch queues.
        '''
        try:
            DEVICEEVENTLOCK.acquire()
            if deviceid in self._fifos:
                del(self._fifos[deviceid])
            if deviceid in self._sent_timers:
                for timer in self._sent_timers[deviceid]:
                    timer.cancel()
                del(self._sent_timers[deviceid])
            DEVICEEVENTLOCK.release()
        except:
            print traceback.format_exc()
            DEVICEEVENTLOCK.release()

    def send_command(self, deviceid, method, value):
        '''
        Send command thru the tellstick, add a new entry to acktosend.
        '''
        self._clean_batch(deviceid)
        self._lastsents[deviceid] = {'method': method,
                            'value' : value}
        self._ackstosend[deviceid] = {'method': method,
                            'value' : value}
        self._telldusd.commands[method](deviceid, value)

    def resend_command(self, deviceid, method, value, active_batch = False):
        '''
        Resend the last command thru the tellstick.
        if method != 0, the new method and value ar set to the new value.
        Usefull when stopping DIO shutter, use method=STOP as new value.
        If active_batch is True, resend the command only if a batch is running.
        '''
        if (active_batch == False) or \
          (active_batch == True and deviceid in self._fifos and len(self._fifos[deviceid]) > 0) :
            if deviceid in self._lastsents :
#                print "resend"
                self._clean_batch(deviceid)
                if method == 0:
                    self._ackstosend[deviceid] = {'method': self._lastsents[deviceid][method],
                                        'value' : self._lastsents[deviceid][value]}
#                    print "resend method=%s" % method
                else:
                    self._fifos[deviceid] = deque()
                    self._fifos[deviceid].append({'method': self._lastsents[deviceid]["method"],
                                        'value' : self._lastsents[deviceid]["value"]})
                    self._ackstosend[deviceid] = {'method': method,
                                        'value' : value}
#                    print "resend change method=%s" % method
                self._telldusd.commands[self._lastsents[deviceid]["method"]](deviceid, self._lastsents[deviceid]["value"])

    def create_batch(self, deviceid, method, value):
        '''
        Create a batch job ( many commands ).
        The parameters are used to send the ack.
        @param id : id of device of the ack to send
        @param method : method of device of the ack to send
        @param value : id of device of the ack to send
        '''
        self._clean_batch(deviceid)
        self._ackstosend[deviceid] = {'method': method,
                            'value' : value}
        self._fifos[deviceid] = deque()
        self._sent_timers[deviceid] = set()

    def _send_batch_timer(self, deviceid, method, value):
        '''
        Used by a timer to send a message.
        @param id : id of device of the ack to send
        @param method : method of device of the ack to send
        @param value : id of device of the ack to send
        '''
        self._lastsents[deviceid] = {'method': method,
                            'value' : value}
        self._telldusd.commands[method](deviceid, value)

    def add_batch(self, deviceid, method, value, delay):
        '''
        Add a job to bacth.
        @param id : id of device
        @param method : method of device
        @param value : value parameter of device
        @param delay : the delay to wait before sending command
        '''
        ##### BUG POSSIBLE
        ##### PROBLEME DE PASSAGE DE PARAMETRE POTENTIEL
        try :
            DEVICEEVENTLOCK.acquire()
            timer = Timer(delay, self._send_batch_timer, [deviceid, method, value])
            self._sent_timers[deviceid].add(timer)
            self._fifos[deviceid].append({'method': method,
                                'value' : value})
            #print "add_batch : deque = %s" % self._fifos[deviceid]
            DEVICEEVENTLOCK.release()
        except :
            print traceback.format_exc()
            DEVICEEVENTLOCK.release()

    def start_batch(self, deviceid, send_ack_now = True):
        '''
        Start the batch job.
        @param id : id of device to start batch job
        '''
        try :
            DEVICEEVENTLOCK.acquire()
            for timer in self._sent_timers[deviceid]:
                timer.start()
            DEVICEEVENTLOCK.release()
            if send_ack_now == True :
                self._parent.send_xpl_ack(deviceid,
                        self._ackstosend[deviceid]["method"],
                        self._ackstosend[deviceid]["value"])
        except :
            print traceback.format_exc()
            DEVICEEVENTLOCK.release()

    def get_last_sent(self, deviceid):
        '''
        Return the last sent command to the tellstick. None otherwise.
        @param id : id of device to return the state
        '''
        if (deviceid in self._lastsents) and (deviceid not in self._fifos):
            #if device in laststents and theer is no running batch
            return self._lastsents[deviceid]
        else :
            return None

    def _receive(self, deviceid, method, value, callbackid):
        '''
        Receive an event fron the callback procedure
        '''
        #print "_receive : deviceid=%s, method=%s, value=%s, callbackid=%s" % (deviceid, method, value, callbackid)
        #print "type value=%s" % (type(value))
        try :
            DEVICEEVENTLOCK.acquire()
                #print "del received_timers"
            if deviceid in self._fifos:
                #There is a running batch for this device
                #print "There is a running batch"
#                print "deque : %s" % self._fifos[deviceid]
#                last = self._fifos[deviceid].popleft()
#                if (last['method'] == method) and (last['value'] == value) :
#                    #The event match
#                    if len(self._fifos[deviceid]) == 0:
#                        #There is no more messages to wait for
#                        #we need to send the ack for the batch
#                        if deviceid in self._fifos:
#                            del(self._fifos[deviceid])
#                            #print "del fifos"
#                        if deviceid in self._sent_timers:
#                            for timer in self._sent_timers[deviceid]:
#                                timer.cancel()
#                            del(self._sent_timers[deviceid])
#                            #print "del sent_timers"
#                        self._parent.send_xpl_ack(deviceid,
#                                self._ackstosend[deviceid]["method"],
#                                self._ackstosend[deviceid]["value"])
                event = {'method': method, 'value' : value}
                #print "Found %s matches in deque" % self._fifos[deviceid].count(event)
                if self._fifos[deviceid].count(event) > 0:
                    self._fifos[deviceid].remove(event)
                    if len(self._fifos[deviceid]) == 0:
                        #There is no more messages to wait for
                        #we need to send the ack for the batch
                        if deviceid in self._fifos:
                            del(self._fifos[deviceid])
                            #print "del fifos"
                        if deviceid in self._sent_timers:
                            for timer in self._sent_timers[deviceid]:
                                timer.cancel()
                            del(self._sent_timers[deviceid])
                            #print "del sent_timers"
                        self._parent.send_xpl_ack(deviceid,
                                self._ackstosend[deviceid]["method"],
                                self._ackstosend[deviceid]["value"])
                    DEVICEEVENTLOCK.release()
                else:
                    #The event doesn't match
                    #We reput it to the left of the deque
                    #and send the message as a trig or cmnd
                    #self._fifos[deviceid].appendleft(last)
                    DEVICEEVENTLOCK.release()
                    #self._parent.send_xpl_new(deviceid, method, value)
            else :
                #This is a simple commande
                #We look in lastsents to see if it match
                #print "Simple command found"
#                print "_lastsents = %s" % self._lastsents[deviceid]
                DEVICEEVENTLOCK.release()
#                print "type value %s" % type(value)
#                print "type self._lastsents[deviceid]['value'] %s" % type(self._lastsents[deviceid]['method'])
                if (deviceid in self._lastsents) and \
                    (self._lastsents[deviceid]['method'] == method) and \
                    (self._lastsents[deviceid]['value'] == value) :
                    #The message match the last sent.
                    #We send a trig for this command
                    self._parent.send_xpl_ack(deviceid,
                            self._ackstosend[deviceid]["method"],
                            self._ackstosend[deviceid]["value"])
                else :
                    #This is a new event.
                    #We need to send a cmnd message (for a ligthing controller)
                    #or a trig message for a sensor
                    #How can we make the difference ???
                    self._parent.send_xpl_new(deviceid, method, value)
            #if self._reset_receive_timer(deviceid, method, value) :
            #    self._del_receive_timer(deviceid, method, value)
            self._create_refuse_timer(deviceid, method, value, callbackid)
        except:
            print traceback.format_exc()
            DEVICEEVENTLOCK.release()

    def receive(self, deviceid, method, value, callbackid):
        '''
        Receive an event fron the callback procedure
        '''
        #print "receive : deviceid=%s, method=%s, value=%s, callbackid=%s" % (deviceid, method, value, callbackid)
        if value == "" or value == None or value == "None" :
            value = 0
        else :
            value = int(value)
        try :
            if self._check_refuse_timer(deviceid, method, value):
                self._reset_receive_timer(deviceid, method, value)
                #start timer with 0.5 second delay (adjust the delay to suit your needs)
                self._create_receive_timer(deviceid, method, value, callbackid)
        except :
            raise TelldusException("Error when receiving data.")

    def _reset_receive_timer(self, deviceid, method, value):
        '''
        Reset a timer if needed
        '''
        try :
            #Try to cancel the timer
            #If it does not exist, th exception is catch silently
            self._received_timers[deviceid][method][value].cancel()
            #self._received_timers[deviceid].cancel()
            return True
        except :
            #print "exception"
            return False

    def _create_receive_timer(self, deviceid, method, value, callbackid):
        '''
        Create a timer
        '''
        #start timer with a delay (adjust the delay to suit your needs)
        timer = Timer(self._delayrf, self._receive, args=[deviceid, method, value, callbackid])
        timer.start()
        self._received_timers[deviceid] = {method : { value : timer}}
        #print "receive_timer for %s:%s:%s created" % (deviceid, method, value)
        #self._received_timers[deviceid] = timer

    def _del_receive_timer(self, deviceid, method, value):
        '''
        Delete a received timer if needed
        '''
        try :
            self._reset_receive_timer(deviceid, method, value)
            del(self._received_timers[deviceid][method][value])
        except :
            pass
        try :
            if len(self._received_timers[deviceid][method]) == 0:
                del(self._received_timers[deviceid][method])
        except :
            pass
        try :
            if len(self._received_timers[deviceid]) == 0:
                del(self._received_timers[deviceid])
        except :
            pass
        #print "receivetimer for %s:%s:%s deleted" % (deviceid, method, value)

    def _create_refuse_timer(self, deviceid, method, value, callbackid):
        '''
        Create a refused timer. While this timer is active, we don't accept
        any more message
        '''
        #start timer with a delay (adjust the delay to suit your needs)
        timer = Timer(self._delayrf, self._del_refuse_timer, args=[deviceid, method, value])
        timer.start()
        self._refused_timers[deviceid] = {method : { value : timer}}
        #print "refused timer for %s:%s:%s created" % (deviceid, method, value)
        #self._received_timers[deviceid] = timer

    def _del_refuse_timer(self, deviceid, method, value):
        '''
        Delete a refused timer if needed
        '''
        if self._reset_receive_timer(deviceid, method, value) :
            self._del_receive_timer(deviceid, method, value)
        try :
            del(self._refused_timers[deviceid][method][value])
        except :
            pass
        try :
            if len(self._refused_timers[deviceid][method]) == 0:
                del(self._refused_timers[deviceid][method])
        except :
            pass
        try :
            if len(self._refused_timers[deviceid]) == 0:
                del(self._refused_timers[deviceid])
        except :
            pass
        #print "refusetimer for %s:%s:%s deleted" % (deviceid, method, value)

    def _check_refuse_timer(self, deviceid, method, value):
        '''
        Check if the queue for this (deviceid,method,value) is opened or not
        '''
        try :
            timer = self._refused_timers[deviceid][method][value]
            return False
        except :
            return True

class Telldusd:
    """
    Interface to the telldusd daemon. It encapsulates ALL the calls to
    the telldus daemon.
    """
    def __init__(self):
        '''
        Init the class
        '''
        self._tdlib = None
        self._device_event_cb = None
        self._device_event_cb_id = None
        self._device_change_event_cb = None
        self._device_change_event_cb_id = None
        ret = find_library("telldus-core")
        if ret != None:
            try:
                if (platform.system() == 'Windows'):
                    #Windows
                    self._tdlib = windll.LoadLibrary(ret)
                else:
                    #Linux
                    self._tdlib = cdll.LoadLibrary(ret)
            except:
                raise TelldusException("Could not load the telldus-core library.")
        else:
            raise TelldusException("Could not find the telldus-core library. Check if it is installed properly.")
        try:
            self._tdlib.tdInit()
        except:
            raise TelldusException("Could not initialize telldus-core library.")
        self.xplcommands = {
            TELLSTICK_TURNON : {'cmd': "on"},
            TELLSTICK_TURNOFF : {'cmd': "off"},
            TELLDUS_BRIGHT : {'cmd': "bright"},
            TELLDUS_SHINE : {'cmd': "shine"},
            TELLDUS_CHANGE : {'cmd': "change"},
            TELLSTICK_BELL : {'cmd': "_bell"},
            TELLSTICK_TOGGLE : {'cmd': "_toggle"},
            TELLSTICK_DIM : {'cmd': "dim"},
            TELLSTICK_LEARN : {'cmd': "_learn"},
            TELLSTICK_EXECUTE : {'cmd': "_execute"},
            TELLSTICK_UP : {'cmd': "up"},
            TELLDUS_SHUT : {'cmd': "shut"},
            TELLSTICK_DOWN : {'cmd': "down"},
            TELLSTICK_STOP : {'cmd': "stop"},
        }
        self.commands = {
            TELLSTICK_TURNON : lambda d, l: self.turn_on(d),
            TELLSTICK_TURNOFF : lambda d, l: self.turn_off(d),
            TELLSTICK_DIM : lambda d, l: self.dim(d, l),
            TELLSTICK_BELL : lambda d, l: self.bell(d),
            TELLSTICK_UP : lambda d, l: self.up(d),
            TELLSTICK_DOWN : lambda d, l: self.down(d),
            TELLSTICK_STOP : lambda d, l: self.stop(d),
        }

    def register_device_event(self, parent):
        '''
        Register the device event callback to telldusd
        '''
        try:
            if (platform.system() == 'Windows'):
                cmpfunc = WINFUNCTYPE(c_void_p, c_int, c_int, c_char_p,
                    c_int, c_void_p)
            else:
                cmpfunc = CFUNCTYPE(c_void_p, c_int, c_int, c_char_p,
                    c_int, c_void_p)
            self._device_event_cb = cmpfunc(device_event_callback)
            self._device_event_cb_id = \
                self._tdlib.tdRegisterDeviceEvent(
                    self._device_event_cb, py_object(parent))
        except:
            raise TelldusException("Could not register the device event callback.")

    def unregister_device_event(self):
        '''
        Unregister the device event callback to telldusd
        '''
        try:
            self._tdlib.UnregisterCallbak(self._device_event_cb_id)
        except:
            raise TelldusException("Could not unregister the device event callback.")

    def register_device_change_event(self, parent):
        '''
        Register the device change event callback to telldusd
        '''
        try:
            if (platform.system() == 'Windows'):
                cmpfunc = WINFUNCTYPE(c_void_p, c_int, c_int, c_int,
                    c_int, c_void_p)
            else:
                cmpfunc = CFUNCTYPE(c_void_p, c_int, c_int, c_int,
                    c_int, c_void_p)
            self._device_change_event_cb = \
                cmpfunc(device_change_event_callback)
            self._device_change_event_cb_id = \
                self._tdlib.tdRegisterDeviceChangeEvent(
                self._device_change_event_cb, py_object(parent))
        except:
            raise TelldusException("Could not register the device change event callback.")

    def unregister_device_change_event(self):
        '''
        Unregister the device change event callback to telldusd
        '''
        try:
            self._tdlib.UnregisterCallbak(self._device_change_event_cb_id)
        except:
            raise TelldusException("Could not unregister the device event change callback.")

    def get_devices(self):
        '''
        Return a list of devices registered in telldus daemon
        '''
        ret = {}
        for i in range(self._tdlib.tdGetNumberOfDevices()):
            iid = self._tdlib.tdGetDeviceId(c_int(i))
            ret[i] = { "name" : c_char_p(self._tdlib.tdGetName(c_int(iid))).value,
                       "house" : c_char_p(self._tdlib.tdGetDeviceParameter(c_int(iid), c_char_p("house"), "")).value,
                       "unit" : c_char_p(self._tdlib.tdGetDeviceParameter(c_int(iid), c_char_p("unit"), "")).value,
                       "model" : "%s" % c_char_p(self._tdlib.tdGetModel(c_int(iid))).value,
                       "protocol" : c_char_p(self._tdlib.tdGetProtocol(c_int(iid))).value
            }
        return ret

    def get_info(self, deviceid):
        '''
        Get the info on the device
        @param deviceid : id of the module
        '''
        sst = []
        sst.append("%s : %s" % \
            (deviceid, c_char_p(self._tdlib.tdGetName(c_int(deviceid))).value))
        sst.append("model : %s" % \
            (c_char_p(self._tdlib.tdGetModel(c_int(deviceid))).value))
        sst.append("protocol : %s" % \
            (c_char_p(self._tdlib.tdGetProtocol(c_int(deviceid))).value))
        sst.append("house : %s / unit: %s" % (c_char_p(self._tdlib.tdGetDeviceParameter(c_int(deviceid), c_char_p("house"), "")).value, \
            c_char_p(self._tdlib.tdGetDeviceParameter(c_int(deviceid), c_char_p("unit"), "")).value))
        sst.append("Methods :")
        ss1, ss2, ss3 = "No", "No", "No"
        if self.methods(deviceid, TELLSTICK_TURNON) \
            == TELLSTICK_TURNON:
            ss1 = "Yes"
        if self.methods(deviceid, TELLSTICK_TURNOFF) \
            == TELLSTICK_TURNOFF:
            ss2 = "Yes"
        if self.methods(deviceid, TELLSTICK_DIM) \
            == TELLSTICK_DIM:
            ss3 = "Yes"
        sst.append("ON : %s / OFF: %s / DIM: %s" % (ss1, ss2, ss3))
        ss1, ss2, ss3, ss4 = "No", "No", "No", "No"
        if self.methods(deviceid, TELLSTICK_BELL) \
            == TELLSTICK_BELL:
            ss1 = "Yes"
        if self.methods(deviceid, TELLSTICK_TOGGLE) \
            == TELLSTICK_TOGGLE:
            ss2 = "Yes"
        if self.methods(deviceid, TELLSTICK_LEARN) \
            == TELLSTICK_LEARN:
            ss3 = "Yes"
        if self.methods(deviceid, TELLSTICK_EXECUTE) \
            == TELLSTICK_EXECUTE:
            ss4 = "Yes"
        sst.append("BELL : %s / TOGGLE: %s / LEARN: %s / EXECUTE: %s" % \
            (ss1, ss2, ss3, ss4))
        ss1, ss2, ss3 = "No", "No", "No"
        if self.methods(deviceid, TELLSTICK_UP) \
            == TELLSTICK_UP:
            ss1 = "Yes"
        if self.methods(deviceid, TELLSTICK_DOWN) \
            == TELLSTICK_DOWN:
            ss2 = "Yes"
        if self.methods(deviceid, TELLSTICK_STOP) \
            == TELLSTICK_STOP:
            ss3 = "Yes"
        sst.append("UP : %s / DOWN: %s / STOP: %s" % (ss1, ss2, ss3))
        return sst

    def check_device(self, device):
        '''

        Check that the device exist in telldusd
        @param device : address of the device. Maybe malformed.
        '''
        try:
            deviceid = int(device[2:])
            name = c_char_p(self._tdlib.tdGetName(c_int(deviceid))).value
            #print "found name = %s" % name
            if name == None or name == "" :
                #print "bad device %s" % device
                return False
            else:
                #print "good device %s" % device
                return True
        except :
            #print "bad device %s" % device
            return False

    def get_device_id(self, device):
        '''
        Retrieve an id from HU address
        @param device : address of the module (ie TS14)
        @return : Id of the device (14)
        '''
        return int(device[2:])

    def get_device(self, deviceid):
        '''
        Retrieve an address device from deviceid
        @param deviceid : id of the device (ie 14)
        @return : address of the device (ie TS14)
        '''
        return 'TS'+str(deviceid)

    def turn_on(self, deviceid):
        '''
        Turns the internal device On
        @param deviceid : id of the module
        '''
        self._tdlib.tdTurnOn(c_int(deviceid))

    def turn_off(self, deviceid):
        '''
        Turns the internal device Off
        @param deviceid : id of the module
        '''
        self._tdlib.tdTurnOff(c_int(deviceid))

    def bell(self, deviceid):
        '''
        Bells the device
        @param deviceid : id of the module
        '''
        self._tdlib.tdBell(c_int(deviceid))

    def learn(self, deviceid):
        '''
        Sends a special Learn command to the device
        @param deviceid : id of the module
        '''
        self._tdlib.tdLearn(c_int(deviceid))

    def dim(self, deviceid, level):
        '''
        Dims the device level should be between 0 and 100
        tdlib use a level from 0 to 255. So we translate it.
        @param deviceid : id of the module
        @param level : level of light
        '''
        self._tdlib.tdDim(c_int(deviceid), c_ubyte(int(level)))

    def up(self, deviceid):
        '''
        Move the shutter up.
        Test if the device support the up command
        If not try to send an on command
        @param deviceid : id of the module
        '''
        self._tdlib.tdUp(c_int(deviceid))

    def down(self, deviceid):
        '''
        Move the shutter down.
        Test if the device support the up command
        If not try to send an on command
        @param deviceid : id of the module
        '''
        self._tdlib.tdDown(c_int(deviceid))

    def stop(self, deviceid):
        '''
        Stop the shutter.
        Test if the device support the up command
        If not try to manage it supporting the on command
        @param deviceid : id of the module
        '''
        self._tdlib.tdStop(c_int(deviceid))

    def methods(self, deviceid, methods):
        '''
        Stop the shutter.
        Test if the device support the up command
        If not try to manage it supporting the on command
        @param deviceid : id of the module
        '''
        #int methods = tdMethods(id, TELLSTICK_TURNON | \
        #    TELLSTICK_TURNOFF | TELLSTICK_BELL);
        return self._tdlib.tdMethods(c_int(deviceid), methods)

class Helpers():
    """
    Encapsulate the helpers
    """

    def __init__(self, telldusd):
        """
        Initialise the helper class
        """
        self._telldusd = telldusd

    def helper_list(self, params = None):
        """
        List all devices
        """
        data = []
        if "devicetype" in params :
#            print "params=%s" % params
            data.append("List all devices of type %s :" % params["devicetype"])
            data.append("id : XPL id : Name")
        else :
            data.append("List all devices : ")
            data.append("id : XPL id : Name")
            # List devices
            devices = self._telldusd.get_devices()
            for key in devices:
                data.append("%s  :  %s  : %s" % (str(key), self._telldusd.get_device(key), devices[key]["name"]))
        return data

    def helper_info(self, params = None):
        """
        Informations about a device
        """
        data = []
        try :
            data.append("Information for device %s : " % params["device"])
            if len(params) == 1:
                data.extend(self._telldusd.get_info(int(params["device"])))
            else:
                data.append("Bad usage of this helper.")
        except :
            data.append("Something get wrong. Check the device address.")
        return data

