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
import time
import platform
import threading
from datetime import datetime
from datetime import timedelta
from collections import deque
from domogik.xpl.lib.telldus_dawndusk import TelldusDawnduskAPI
from domogik.xpl.lib.telldus_windoor import TelldusWindoorAPI
from domogik.xpl.lib.telldus_move import TelldusMoveAPI

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
TELLDUS_SHUT = 201

DEVICEEVENTLOCK = threading.Lock()
QUEUELOCK = threading.Lock()

#def sensor_event_callback(protocol, model, deviceid, datatype, \
#    '''
#    Add Device to the dictionnary
#    '''
#    value, timestamp, callbackid, context):
#    print "sensorEventCallback: id=%s, method=%s and data=%s" % \
#        (deviceid, model, value)

def device_event_callback(deviceid, method, value, callbackid,
    context):
    '''
    Add Device to the dictionnary
    '''
    if deviceid == 0 or method == 0 :
        return
    obj = cast(context, py_object).value
    obj.log.debug("deviceEventCallback: id=%s, method=%s and value=%s" %
        (deviceid, method, value))
    eventdate = datetime.now()
    DEVICEEVENTLOCK.acquire()
    obj.send_xpl(deviceid, method, c_char_p(value).value, callbackid,
        eventdate)
    DEVICEEVENTLOCK.release()

def device_change_event_callback(deviceid, changeevent,
    changetype, callbackid, context):
    '''
    Add Device to the dictionnary
    '''
    obj = cast(context, py_object).value
    obj.log.debug("deviceChangeEventCallback: id=%s, changeEvent=%s and \
        changeType=%s" % (deviceid, changeevent, changetype))
    obj.load_devices()

class DeviceEventQueue:
    '''
    Add Device to the dictionnary
    '''
    def __init__(self, delay_rf):
        '''
        Add Device to the dictionnary
        '''
        self._delay_rf = delay_rf
        self._data = dict()

    def add_device(self, deviceid, method, value, callbackid, eventdate):
        '''
        Add Device to the dictionnary
        '''
        self._data[deviceid] = {'method': method,
                            'value' : value,
                            'callbackid' : callbackid,
                            'eventDate' : eventdate
                            }
        #print deviceid,self._data[deviceid]

    def equal(self, deviceid, method, value, callbackid, eventdate):
        '''
        Add Device to the dictionnary
        '''
        if (deviceid in self._data and
            self._data[deviceid]['method'] == method and
            self._data[deviceid]['value'] == value and
            self._data[deviceid]['callbackid'] == callbackid and
            (eventdate-self._data[deviceid]['eventDate'] <
                timedelta(milliseconds=self._delay_rf))):
            #print "EQUAL !!!!!!"
            return True
        else:
            #print "NOT EQUAL !!!!!!"
            self.add_device(deviceid, method, value, callbackid, eventdate)
            return False

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

class TelldusDevices:
    '''
    Add Device to the dictionnary
    '''

    def __init__(self):
        '''
        Add Device to the dictionnary
        '''
        self._data = dict()

    def add_device(self, deviceid, name, protocol, model, house,
        unit, devicetype, param1, param2):
        '''
        Add Device to the dictionnary
        '''
        self._data[deviceid] = {'protocol': protocol,
                            'name' : name,
                            'model' : model,
                            'house' : house,
                            'unit' : unit,
                            'devicetype' : devicetype,
                            'param1' : param1,
                            'param2' : param2,
                            }
        #print deviceid,self._data[deviceid]

    def get_id(self, add):
        '''
        Retrieve an id from HU address
        '''
        return int(add[2:])

    def get_address(self, deviceid):
        '''
        Retrieve an address from deviceid
        '''
        return 'TS'+str(deviceid)

    def get_name(self, deviceid):
        '''
        Retrieve an address from deviceid
        '''
        return str(self._data[deviceid]['name'])

    def get_devicetype(self, deviceid):
        '''
        Retrieve a device type deviceid
        '''
        return str(self._data[deviceid]['devicetype'])

    def get_device(self, deviceid):
        '''
        Retrieve an Device from from deviceid
        @param deviceid : deviceid of the module (given by telldus-core)
        '''
        return self._data[deviceid]

class TelldusXPL:
    '''
    Manage the extended XPL language
    ie : shutter -> on, shutter close during 8s(t/2)
    We will scan the incoming messages from the tellstick
    and reassemble them in a complex XPL command
    '''
    def __init__(self, callback):
        self._data = dict()
        self._callback = callback

    def append(self, deviceid, method):
        '''
        Append Device to the dictionnary/list
        '''
        QUEUELOCK.acquire()
        if deviceid not in self._data :
            queue = deque()
        else:
            queue = self._data[deviceid]
        queue.append({'deviceid': deviceid,
                            'method' : method,
                            })
        self._data[deviceid] = queue
        #print deviceid,self._data[deviceid]
        QUEUELOCK.release()

    def clear(self, deviceid):
        '''
        Clear the queue of the device
        Send an ACK for the complex command.
        '''
        QUEUELOCK.acquire()
        if deviceid not in self._data :
            #print False
            QUEUELOCK.release()
            return False
        queue = self._data[deviceid]
        ttrue = True
        while ttrue:
            elt = queue.popleft()
            if self.count(deviceid) == 0:
                #Yes. This is the complex command
                #We send an XPL message to ack the complex command
                self._callback(elt['deviceid'], elt['method'])
                del self._data[deviceid]
                ttrue = False
        QUEUELOCK.release()

    def left_command(self, deviceid):
        '''
        Return the left command in the queue
        '''
        QUEUELOCK.acquire()
        if deviceid not in self._data :
            #print False
            QUEUELOCK.release()
            return 0
        queue = self._data[deviceid]
        elt = queue.popleft()
        queue.appendleft(elt)
        #print "leftCommand : %s" % elt['method']
        QUEUELOCK.release()
        return elt['method']

    def in_queue(self, deviceid, method):
        '''
        Validate that the message is a part of a complex XPL message
        '''
        #print deviceid,self._data[deviceid]
        QUEUELOCK.acquire()
        if deviceid not in self._data :
            #print False
            QUEUELOCK.release()
            return False
        queue = self._data[deviceid]
        elt = queue.popleft()
        if (elt['deviceid']==deviceid) and (elt['method']==method):
            #The message is in the queue. We pop it so we remove it
            #Now we must test if there is only one item in the queue
            if self.count(deviceid)==1:
                #Yes. This is the complex command
                #We send an XPL message to ack the complex command
                elt2 = queue.popleft()
                self._callback(elt2['deviceid'], elt2['method'])
                del self._data[deviceid]
            else:
                #There is many commands in the list ...
                self._data[deviceid] = queue
        else :
            #Well don't know where this message came from
            #we put the message in the queue
            queue.appendleft(elt)
            self._data[deviceid] = queue
        #print True
        QUEUELOCK.release()
        return True

    def validate(self, deviceid, method):
        '''
        Validate that the message is not a part of a complex XPL message
        DEPRECATED Use inQueue instead
        '''
        if deviceid not in self._data :
            #print True
            return True
        #print deviceid,self._data[deviceid]
        queue = self._data[deviceid]
        elt = queue.popleft()
        if (elt['deviceid'] == deviceid) and (elt['method'] == method):
            #The message is in the queue. We pop it so we remove it
            #Now we must test if there is only one item in the queue
            if self.count(deviceid) == 1:
                #Yes. This is the complex command
                #We send an XPL message to ack the complex command
                elt2 = queue.popleft()
                self._callback(elt2['deviceid'], elt2['method'])
                del self._data[deviceid]
            else:
                #There is many commands in the list ...
                self._data[deviceid] = queue
        else :
            #Well don't know where this message came from
            #we put the message in the queue
            queue.appendleft(elt)
            self._data[deviceid] = queue
        #print False
        return False

    def count(self, deviceid):
        '''
        Count the number of messages for a device in the queue
        '''
        if deviceid not in self._data :
            #print True
            return 0
        else :
            return len(self._data[deviceid])

class TelldusAPI:
    '''
    Telldus python binding library
    '''
    def __init__(self, xplcallback, log, config, xplsender):
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
        self._xpl_callback = xplcallback
        self._tdlib = None
        self.myxpl = xplsender
        self.log.info("telldusAPI.__init__ : Look for telldus-core")
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
                self.log.exception("telldusAPI.__init__ : Could not \
                    load the telldus-core library.")
                raise TelldusException("Could not load the telldus-core \
                    library.")
        else:
            self.log.error("telldusAPI.__init__ : Could not find the \
                telldus-core library. Check if it is installed properly.")
            raise TelldusException("Could not find the telldus-core \
                library. Check if it is installed properly.")
        # Initialize tellDus API
        try:
            self._tdlib.tdInit()
        except:
            self.log.exception("telldusAPI.__init__ : Could not init \
                telldus-core library.")
            raise TelldusException("Could not init telldus-core library.")
        self._devices = None
        self.load_devices()
        self._commands = None
        self.load_commands()
        self._ext_dawndusk = False
        self._dawndusk = None
        self._ext_windoor = False
        self._windoor = None
        self._ext_move = False
        self._move = None
        self.load_telldus_extensions()
        self._last_sent_command = {}
        if self.config == None:
            self.log.warning("telldusAPI.__init__ : Receiver is disabled.")
        else:
            try:
                self._delay_rf = int(self.config.query('telldus', 'delayrf'))
            except:
                self.log.exception("telldusAPI.__init__ : Can't get \
                    configuration from XPL")
                self._delay_rf = 400
                #print "self=%s" % param
            self.log.debug("telldusAPI.__init__ : Registering the \
                callback functions ...")
            if (platform.system() == 'Windows'):
                cmpfunc = WINFUNCTYPE(c_void_p, c_int, c_int, c_char_p,
                    c_int, c_void_p)
            else:
                cmpfunc = CFUNCTYPE(c_void_p, c_int, c_int, c_char_p,
                    c_int, c_void_p)
            self._device_event_callback = cmpfunc(device_event_callback)
            self._device_event_callback_id = \
                self._tdlib.tdRegisterDeviceEvent(
                    self._device_event_callback, py_object(self))
            self._device_event_queue = DeviceEventQueue(self._delay_rf)
            if (platform.system() == 'Windows'):
                cmpfunc = WINFUNCTYPE(c_void_p, c_int, c_int, c_int,
                    c_int, c_void_p)
            else:
                cmpfunc = CFUNCTYPE(c_void_p, c_int, c_int, c_int,
                    c_int, c_void_p)
            self._device_change_event_callback = \
                cmpfunc(device_change_event_callback)
            self._device_change_event_id = \
                self._tdlib.tdRegisterDeviceChangeEvent(
                self._device_change_event_callback, py_object(self))
            self._telldus_xpl = TelldusXPL(self._call_xpl_callback)
        self.log.debug("telldusAPI.__init__ : Done :-)")

    def reload_config(self):
        '''
        Load devices into the _devices dictionnary
        '''
        self.log.debug("telldusAPI.reloadConfig : Start")
        if self.config != None:
            try:
                self._delay_rf = int(self.config.query('telldus', 'delayrf'))
            except:
                self.log.exception("telldusAPI.__init__ : Can't get \
                    configuration from XPL")
                self._delay_rf = 400
        self.load_devices()
        self.load_telldus_extensions()
        self.log.debug("telldusAPI.reloadConfig : Done :-)")

    def load_devices(self):
        '''
        Load devices into the _devices dictionnary
        '''
        self.log.debug("telldusAPI._loadDevices : Start ...")
        self._devices = TelldusDevices()
        #Read the plugin configurations
        confs = {}
        if self.config != None :
            num = 1
            loop = True
            while loop == True:
                name = self.config.query('telldus', 'name-%s' % str(num))
                devicetype = self.config.query('telldus',
                    'devicetype-%s' % str(num))
                param1 = self.config.query('telldus', 'param1-%s' % str(num))
                param2 = self.config.query('telldus', 'param2-%s' % str(num))
                if name != None:
                    self.log.debug("telldusAPI._loadDevices : \
                        Configuration from xpl : name=%s, param1=%s, \
                        param2=%s" % (name, param1, param2))
                    confs[name] = {"devicetype" : devicetype,
                        "param1" : param1, "param2" : param2}
                else:
                    loop = False
                num += 1
        #Read the devices from telldus-core
        j = 0
        for i in range(self._tdlib.tdGetNumberOfDevices()):
            j = j+1
            iid = self._tdlib.tdGetDeviceId(c_int(i))
            #print iid
            id_name = c_char_p(self._tdlib.tdGetName(c_int(iid))).value
            id_house = c_char_p(self._tdlib.tdGetDeviceParameter( \
                c_int(iid), c_char_p("house"), "")).value
            id_unit = c_char_p(self._tdlib.tdGetDeviceParameter(c_int(iid),
                c_char_p("unit"), "")).value
            id_model = c_char_p(self._tdlib.tdGetModel(
                c_int(iid))).value.partition(':')[0]
            id_protocol = c_char_p(self._tdlib.tdGetProtocol(
                c_int(iid))).value
            id_devicetype = None
            id_param1 = None
            id_param2 = None
            if self._devices.get_address(iid) in confs.iterkeys():
                self.log.debug("telldusAPI._loadDevices : Get \
                    configuration from plugin : device=%s" \
                    % (self._devices.get_address(iid)))
                id_devicetype = confs[self._devices.get_address(iid)]\
                    ['devicetype']
                id_param1 = confs[self._devices.get_address(iid)]['param1']
                id_param2 = confs[self._devices.get_address(iid)]['param2']
            self._devices.add_device(iid, id_name, id_protocol, id_model, \
                id_house, id_unit, id_devicetype, id_param1, id_param2)
        self.log.debug("telldusAPI._loadDevices : Loading %s devices \
            from telldus-core." % j)
        self.log.debug("telldusAPI._loadDevices : Done :-)")

    def load_telldus_extensions(self):
        """
        Load the extensions
        """
        if self.config != None :
            self._load_telldus_windoor()
            self._load_telldus_dawndusk()
            self._load_telldus_move()

    def _load_telldus_windoor(self):
        """
        Load the WINDOOR extension
        """
        self._windoor = None
        boo = self.config.query('telldus', 'windoor')
        if boo == None:
            boo = "False"
        self._ext_windoor = eval(boo)
        self.log.debug("telldus.load_telldus_windoor : Load =" +
            str(type(self._ext_windoor)))
        if self._ext_windoor == True:
            self.log.debug("telldus.load_telldus_windoor : \
                Load windoor extension")
            try:
                self._windoor = TelldusWindoorAPI(self)
            except Exception:
                self.log.exception("Something went wrong during windoor\
                    extension init, check logs")
        else:
            self.log.debug("telldus.load_telldus_windoor : Don't load \
                windoor extension")

    def _load_telldus_dawndusk(self):
        """
        Load the DAWNDUSK extension
        """
        self._dawndusk = None
        boo = self.config.query('telldus', 'dawndusk')
        if boo == None:
            boo = "False"
        self._ext_dawndusk = eval(boo)
        if self._ext_dawndusk == True:
            self.log.debug("telldus.load_telldus_dawndusk : Load \
                dawndusk extension")
            try:
                self._dawndusk = TelldusDawnduskAPI(self)
            except Exception:
                self.log.exception("Something went wrong during dawndusk\
                    extension init, check logs")
        else:
            self.log.debug("telldus.load_telldus_dawndusk : Don't load\
                dawndusk extension")

    def _load_telldus_move(self):
        """
        Load the MOVE extension
        """
        self._move = None
        boo = self.config.query('telldus', 'move')
        if boo == None:
            boo = "False"
        self._ext_move = eval(boo)
        if self._ext_move == True:
            self.log.debug("telldus.load_telldus_move : Load move\
                extension")
            try:
                self._move = TelldusMoveAPI(self)
            except Exception:
                self.log.exception("Something went wrong during move \
                    extension init, check logs")
        else:
            self.log.debug("telldus.load_telldus_move : Don't load \
                move extension")

    def load_commands(self):
        """
        Load commands into a dictionnary
        """
        self.log.debug("telldusAPI._loadCommands : Start ...")
        self._commands = dict()
        if self._tdlib == None:
            self.log.error("Library telldus-core not loaded.")
            raise TelldusException("Library telldus-core not loaded.")
        self._commands[TELLSTICK_TURNON] = {'cmd': "on"}
        self._commands[TELLSTICK_TURNOFF] = {'cmd': "off"}
        self._commands[TELLDUS_BRIGHT] = {'cmd': "bright"}
        self._commands[TELLSTICK_BELL] = {'cmd': "_bell"}
        self._commands[TELLSTICK_TOGGLE] = {'cmd': "_toggle"}
        self._commands[TELLSTICK_DIM] = {'cmd': "dim"}
        self._commands[TELLSTICK_LEARN] = {'cmd': "_learn"}
        self._commands[TELLSTICK_EXECUTE] = {'cmd': "_execute"}
        self._commands[TELLSTICK_UP] = {'cmd': "up"}
        self._commands[TELLDUS_SHUT] = {'cmd': "shut"}
        self._commands[TELLSTICK_DOWN] = {'cmd': "down"}
        self._commands[TELLSTICK_STOP] = {'cmd': "stop"}
        self.log.debug("telldusAPI._loadCommands : Done :-)")

    def send_xpl(self, deviceid, method, value, callbackid, eventdate):
        """
        Send messages from Tellstick to xpl
        @param deviceid : the id of the transceiver
        @param method : the command sent
        @param value : the value sent
        @param callbackid : the id of the callback
        @param eventdate : the date of the event. Use to filter redondant events.
        """
        self.log.debug("telldusAPI.send_xpl : Start ...")
        #Try to test the message is not repeated
        if self._device_event_queue.equal(deviceid, method, value, \
            callbackid, eventdate)==False:
            #It is not
            #Test if the message is not a part of the complex message
            if self._telldus_xpl.in_queue(deviceid, method)==False:
                #print self.isDevicetype(deviceid,self._dawndusk.devicetype)
                self.send_xpl_extensions(deviceid, method, value, \
                    callbackid, eventdate)
                self._call_xpl_callback(deviceid, method)
        self.log.debug("telldusAPI.send_xpl : Done")

    def send_xpl_extensions(self, deviceid, method, value, callbackid, \
        eventdate):
        """
        Send messages extensions
        @param deviceid : the id of the transceiver
        @param method : the command sent
        @param value : the value sent
        @param callbackid : the id of the callback
        @param eventDate : the date of the event. Use to filter redondant events.
        """
        self.log.debug("telldusAPI.send_xpl_extensions : Start ...")
        if self._ext_dawndusk == True and self.is_devicetype(deviceid, \
            self._dawndusk.devicetype) == True:
            self.log.debug("telldusAPI.send_xpl : Use the danwdusk extension")
            self._dawndusk.send_dawndusk(deviceid, method)
        elif self._ext_windoor == True and \
            self.is_devicetype(deviceid, self._windoor.devicetype) == True:
            self.log.debug("telldusAPI.send_xpl : Use the windoor extension")
            self._windoor.send_windoor(deviceid, method)
        elif self._ext_move == True and \
            self.is_devicetype(deviceid, self._move.devicetype) == True:
            self.log.debug("telldusAPI.send_xpl : Use the move extension")
            self._move.send_move(deviceid, method)
        self.log.debug("telldusAPI.send_xpl_extensions : Done")

    def _call_xpl_callback(self, deviceid, method):
        """
        Call the xplCallback function
        @param deviceid : the id of the transceiver
        @param method : the command sent
        """
        self.log.debug("telldusAPI._call_xplCallback : Start ...")
        self._xpl_callback(self._devices.get_address(deviceid), \
            self._commands[method]['cmd'])
        self.log.debug("telldusAPI._call_xplCallback : Done")

    def __del__(self):
        '''
        Destructor : Cleanup Telldus Lib
        '''
        self.log.debug("telldusAPI.__del__")

#    def get_devices(self):
#        '''
#        Return the collection of the devices
#        @return : a the collection of devices
#        '''
#        return self._devices._data

    def get_devices_from_type(self, devicetype):
        '''
        Return a collection of devices of type devicetype
        @param devicetype : the device type looking for
        @return : a the collection of devices
        '''
        return None

    def is_devicetype(self, deviceid, devicetype):
        '''
        Test if a device is of device type devicetype
        @param deviceid : the id of the device
        @param devicetype : the device type
        @return : True or False
        '''
        return self._devices.get_devicetype(deviceid) == devicetype

    def get_device_id(self, add):
        '''
        Retrieve an id from HU address
        @param add : address of the module (ie TS14)
        @return : Id of the device
        '''
        return self._devices.get_id(add)

    def get_device_address(self, deviceid):
        '''
        Retrieve an address from id
        @param deviceid : id of the module (given by telldus-core)
        '''
        return self._devices.get_address(deviceid)

    def get_device(self, deviceid):
        '''
        Retrieve an Device from from id
        @param deviceid : id of the module (given by telldus-core)
        '''
        return self._devices.get_device(deviceid)

    def get_device_name(self, deviceid):
        '''
        Retrieve an Device from from id
        @param deviceid : id of the module (given by telldus-core)
        '''
        return self._devices.get_device(deviceid)['name']

    def print_it(self):
        '''
        Test only method
        '''
        print " telldusAPI print is Ok"

    def send_on(self, add):
        '''
        Turns the specified device On
        @param add : address of the module (ie TS14)
        '''
        #print " ON : address: %s" % (add)
        self._turn_on_device(self.get_device_id(add))

    def send_off(self, add):
        '''
        Turns the specified device Off
        @param add : address of the module (ie TS14)
        '''
        #print " OFF : address: %s" % (add)
        self._turn_off_device(self.get_device_id(add))

    def send_dim(self, add, level):
        '''
        Sets the specified dim level on device
        Level should be between 0 and 100
        @param add : address of the module (ie TS14)
        @param level : level of light (0..100)
        '''
        #print "dim level=%s"%type(level)
        level = int(level)
        #print "dim level=%s"%type(level)
        if level <= 0:
            self._turn_off_device(self.get_device_id(add))
        elif level >= 100:
            self._turn_on_device(self.get_device_id(add))
        elif level > 0 and level < 100 :
            self._dim_device(self.get_device_id(add), int(level))

    def send_bright(self, add, level):
        '''
        Turn on the device and after set the specified dim level on device
        Level should be between 0 and 255
        @param add : address of the module (ie TS14)
        @param level : level of light (0..255max)
        '''
        #print " BRIGHT : address: %s, level: %s" % (add,level)
        deviceid = self.get_device_id(add)
        self._telldus_xpl.append(deviceid, TELLSTICK_TURNON)
        self._telldus_xpl.append(deviceid, TELLSTICK_DIM)
        self._telldus_xpl.append(deviceid, TELLDUS_BRIGHT)
        self._turn_on_device(deviceid)
        self._dim_device(deviceid, int(level))

    def send_bell(self, add):
        '''
        Sends the bell signal to device
        @param add : address of the module (ie TS14)
        '''
        self._bell_device(self.get_device_id(add))

    def send_learn(self, add):
        '''
        Sends the special learn command to device
        @param add : address of the module (ie TS14)
        '''
        self._learn_device(self.get_device_id(add))

    def send_up(self, add):
        '''
        Move the shutter up.
        @param add : address of the module (ie TS14)
        '''
        #print " up : address: %s" % (add)
#        self._up_device(self.get_device_id(add))
        deviceid = self.get_device_id(add)
        if self._device_methods(deviceid, TELLSTICK_UP) == TELLSTICK_UP:
            self._up_device(deviceid)
        elif self._device_methods(deviceid, TELLSTICK_TURNON) \
            == TELLSTICK_TURNON:
            dtime = self._devices.get_device(deviceid)['param1']
            if dtime == None:
                dtime = 15
            self._telldus_xpl.append(deviceid, TELLSTICK_TURNON)
            self._telldus_xpl.append(deviceid, TELLSTICK_TURNON)
            self._telldus_xpl.append(deviceid, TELLSTICK_UP)
            self._turn_on_device(deviceid)
            time.sleep(1.2*int(dtime))
            if self._telldus_xpl.count(deviceid)!=0:
                self._turn_on_device(deviceid)
                self.log.debug("telldusAPI.sendUp continue")
            else:
                self.log.debug("telldusAPI.sendUp cancelled")

    def send_down(self, add):
        '''
        Move the shutter down.
        @param add : address of the module (ie TS14)
        '''
        #print " down : address: %s" % (add)
#        self._downDevice(self.get_device_id(add))
        deviceid = self.get_device_id(add)
        if self._device_methods(deviceid, TELLSTICK_DOWN) == TELLSTICK_DOWN:
            self._down_device(deviceid)
        elif self._device_methods(deviceid, TELLSTICK_TURNOFF) \
            == TELLSTICK_TURNOFF:
            dtime = self._devices.get_device(deviceid)['param1']
            if dtime == None:
                dtime = 15
            self._telldus_xpl.append(deviceid, TELLSTICK_TURNOFF)
            self._telldus_xpl.append(deviceid, TELLSTICK_TURNOFF)
            self._telldus_xpl.append(deviceid, TELLSTICK_DOWN)
            self._turn_off_device(deviceid)
            time.sleep(1.2*int(dtime))
            if self._telldus_xpl.count(deviceid)!=0:
                self._turn_off_device(deviceid)
                self.log.debug("telldusAPI.sendUp continue")
            else:
                self.log.debug("telldusAPI.sendDown cancelled")

    def send_shut(self, add, level):
        '''
        Open the shutter depending on level
        Level should be between 0 and 4
        @param add : address of the module (ie TS14)
        @param level : level of light (0..255max)
        '''
        #print " SHUT : address: %s, level: %s" % (add,level)
        #Shutters don't have the same up and down time
        #Try to correct it ...
        up_start = 1.5
        up_factor = 1
        down_factor = 0.9
        level = 3
        deviceid = self.get_device_id(add)
        dtime = self._devices.get_device(deviceid)['param1']
        if dtime == None or dtime == 0:
            dtime = 15
        if level == 0:
            self._telldus_xpl.append(deviceid, TELLSTICK_TURNOFF)
            self._telldus_xpl.append(deviceid, TELLDUS_SHUT)
            self._turn_off_device(deviceid)
        elif level < 3 and level > 0:
            self._telldus_xpl.append(deviceid, TELLSTICK_TURNOFF)
            self._telldus_xpl.append(deviceid, TELLSTICK_TURNON)
            self._telldus_xpl.append(deviceid, TELLSTICK_TURNON)
            self._telldus_xpl.append(deviceid, TELLDUS_SHUT)
            self._turn_off_device(deviceid)
            time.sleep(1.2*int(dtime))
            if self._telldus_xpl.count(deviceid)!=0:
                self._turn_on_device(deviceid)
                time.sleep(up_start+int(dtime)*up_factor*level*25/100)
            if self._telldus_xpl.count(deviceid)!=0:
                self._turn_on_device(deviceid)
        elif level == 3:
            self._telldus_xpl.append(deviceid, TELLSTICK_TURNON)
            self._telldus_xpl.append(deviceid, TELLSTICK_TURNOFF)
            self._telldus_xpl.append(deviceid, TELLSTICK_TURNOFF)
            self._telldus_xpl.append(deviceid, TELLDUS_SHUT)
            self._turn_on_device(deviceid)
            time.sleep(1.2*int(dtime))
            if self._telldus_xpl.count(deviceid)!=0:
                self._turn_off_device(deviceid)
                time.sleep(int(dtime)*down_factor*(4-level)*25/100)
            if self._telldus_xpl.count(deviceid)!=0:
                self._turn_off_device(deviceid)
        elif level == 4:
            self._telldus_xpl.append(deviceid, TELLSTICK_TURNON)
            self._telldus_xpl.append(deviceid, TELLDUS_SHUT)
            self._turn_on_device(deviceid)

    def send_stop(self, add):
        '''
        Stop the shutter.
        @param add : address of the module (ie TS14)
        '''
        #print " stop : address: %s" % (add)
        deviceid = self.get_device_id(add)
        if self._device_methods(deviceid, TELLSTICK_STOP) == TELLSTICK_STOP:
            #If the device support the stop method, use it
            print "Last sent = STOP"
            self._stop_device(deviceid)
            return
        #Well. This is a complex method
        if self._telldus_xpl.left_command(deviceid) == TELLSTICK_TURNOFF:
            # There is pending action with this method
            # we remove it, stop the device and send the xpl ack
            print "Last sent = TURNOFF"
            self._turn_off_device(deviceid)
            self._telldus_xpl.clear(deviceid)
            self._call_xpl_callback(deviceid, TELLSTICK_STOP)
        elif self._telldus_xpl.left_command(deviceid) == TELLSTICK_TURNON:
            # There is pending action with this method
            # we remove it, stop the device and send the xpl ack
            print "Last sent = TURNON"
            self._turn_on_device(deviceid)
            self._telldus_xpl.clear(deviceid)
            self._call_xpl_callback(deviceid, TELLSTICK_STOP)
        elif self._telldus_xpl.left_command(deviceid) == TELLSTICK_UP:
            # There is pending action with this method
            # we remove it, stop the device and send the xpl ack
            print "Last sent = UP"
            self._up_device(deviceid)
            self._telldus_xpl.clear(deviceid)
            self._call_xpl_callback(deviceid, TELLSTICK_STOP)
        elif self._telldus_xpl.left_command(deviceid) == TELLSTICK_DOWN:
            # There is pending action with this method
            # we remove it, stop the device and send the xpl ack
            print "Last sent = DOWN"
            self._down_device(deviceid)
            self._telldus_xpl.clear(deviceid)
            self._call_xpl_callback(deviceid, TELLSTICK_STOP)

    def get_info(self, deviceid):
        '''
        Get the info on the device
        @param deviceid : id of the module
        '''
        if self._tdlib == None:
            self.log.error("Library telldus-core not loaded.")
            raise TelldusException("Library telldus-core not loaded.")
        sst = []
        sst.append("%s : %s" % \
            (deviceid, self._devices.get_device(deviceid)['name']))
        sst.append("model : %s" % \
            (self._devices.get_device(deviceid)['model']))
        sst.append("protocol : %s" % \
            (self._devices.get_device(deviceid)['protocol']))
        sst.append("house : %s / unit: %s" % \
            (self._devices.get_device(deviceid)['house'], \
            self._devices.get_device(deviceid)['unit']))
        sst.append("Methods :")
        ss1, ss2, ss3 = "No", "No", "No"
        if self._device_methods(deviceid, TELLSTICK_TURNON) \
            == TELLSTICK_TURNON:
            ss1 = "Yes"
        if self._device_methods(deviceid, TELLSTICK_TURNOFF) \
            == TELLSTICK_TURNOFF:
            ss2 = "Yes"
        if self._device_methods(deviceid, TELLSTICK_DIM) \
            == TELLSTICK_DIM:
            ss3 = "Yes"
        sst.append("ON : %s / OFF: %s / DIM: %s" % (ss1, ss2, ss3))
        ss1, ss2, ss3, ss4 = "No", "No", "No", "No"
        if self._device_methods(deviceid, TELLSTICK_BELL) \
            == TELLSTICK_BELL:
            ss1 = "Yes"
        if self._device_methods(deviceid, TELLSTICK_TOGGLE) \
            == TELLSTICK_TOGGLE:
            ss2 = "Yes"
        if self._device_methods(deviceid, TELLSTICK_LEARN) \
            == TELLSTICK_LEARN:
            ss3 = "Yes"
        if self._device_methods(deviceid, TELLSTICK_EXECUTE) \
            == TELLSTICK_EXECUTE:
            ss4 = "Yes"
        sst.append("BELL : %s / TOGGLE: %s / LEARN: %s / EXECUTE: %s" % \
            (ss1, ss2, ss3, ss4))
        ss1, ss2, ss3 = "No", "No", "No"
        if self._device_methods(deviceid, TELLSTICK_UP) \
            == TELLSTICK_UP:
            ss1 = "Yes"
        if self._device_methods(deviceid, TELLSTICK_DOWN) \
            == TELLSTICK_DOWN:
            ss2 = "Yes"
        if self._device_methods(deviceid, TELLSTICK_STOP) \
            == TELLSTICK_STOP:
            ss3 = "Yes"
        sst.append("UP : %s / DOWN: %s / STOP: %s" % (ss1, ss2, ss3))
        return sst

    def _turn_on_device(self, deviceid):
        '''
        Turns the internal device On
        @param deviceid : id of the module
        '''
        self._last_sent_command[deviceid] = TELLSTICK_TURNON
        self._tdlib.tdTurnOn(c_int(deviceid))

    def _turn_off_device(self, deviceid):
        '''
        Turns the internal device Off
        @param deviceid : id of the module
        '''
        self._last_sent_command[deviceid] = TELLSTICK_TURNOFF
        self._tdlib.tdTurnOff(c_int(deviceid))

    def _bell_device(self, deviceid):
        '''
        Bells the device
        @param deviceid : id of the module
        '''
        self._last_sent_command[deviceid] = TELLSTICK_BELL
        self._tdlib.tdBell(c_int(deviceid))

    def _learn_device(self, deviceid):
        '''
        Sends a special Learn command to the device
        @param deviceid : id of the module
        '''
        self._last_sent_command[deviceid] = TELLSTICK_LEARN
        self._tdlib.tdLearn(c_int(deviceid))

    def _dim_device(self, deviceid, level):
        '''
        Dims the device level should be between 0 and 100
        tdlib use a level from 0 to 255. So we translate it.
        @param deviceid : id of the module
        @param level : level of light (0..100)
        '''
        #print " DIM : device: %s, level: %s / %s" % \
        #    (deviceid,level,type(level))
        self._last_sent_command[deviceid] = TELLSTICK_DIM
        self._tdlib.tdDim(c_int(deviceid), c_ubyte(int(level*2.55)))

    def _up_device(self, deviceid):
        '''
        Move the shutter up.
        Test if the device support the up command
        If not try to send an on command
        @param deviceid : id of the module
        '''
        self._last_sent_command[deviceid] = TELLSTICK_UP
        self._tdlib.tdUp(c_int(deviceid))

    def _down_device(self, deviceid):
        '''
        Move the shutter down.
        Test if the device support the up command
        If not try to send an on command
        @param deviceid : id of the module
        '''
        self._last_sent_command[deviceid] = TELLSTICK_DOWN
        self._tdlib.tdDown(c_int(deviceid))

    def _stop_device(self, deviceid):
        '''
        Stop the shutter.
        Test if the device support the up command
        If not try to manage it supporting the on command
        @param deviceid : id of the module
        '''
        self._last_sent_command[deviceid] = TELLSTICK_STOP
        self._tdlib.tdStop(c_int(deviceid))

    def _device_methods(self, deviceid, methods):
        '''
        Stop the shutter.
        Test if the device support the up command
        If not try to manage it supporting the on command
        @param deviceid : id of the module
        '''
        #int methods = tdMethods(id, TELLSTICK_TURNON | \
        #    TELLSTICK_TURNOFF | TELLSTICK_BELL);
        return self._tdlib.tdMethods(c_int(deviceid), methods)

if __name__ == "__main__":
    print("TellStick Python binding Class")
    print("Testing mode.\n")
    print("..Creating TellStick object")
    TELL = TelldusAPI()
    print("..OK")
    print("..Sending a ON command")
    TELL.send_on(3)
    print("..OK")
    print("..Sending a OFF command")
    TELL.send_off(3)
    print("..OK")
    print("\nAll is OK")
