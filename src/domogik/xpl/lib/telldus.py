#!/usr/bin/python
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
Prototypes :
 sendOn(deviceId)
 sendOff(deviceId)
 sendDim(deviceId, level)
 sendLearn(deviceId)
 sendBell(deviceId)

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
import ctypes
from ctypes import *
from ctypes.util import find_library
import time
import platform
import threading
from datetime import datetime
from datetime import timedelta
from collections import deque
from domogik.xpl.lib.telldus_dawndusk import *
from domogik.xpl.lib.telldus_windoor import *
from domogik.xpl.lib.telldus_move import *

#platform specific imports:
if (platform.system() == 'Windows'):
        #Windows
        from ctypes import windll, WINFUNCTYPE
else:
        #Linux
        from ctypes import cdll, CFUNCTYPE

# Device methods
TELLSTICK_TURNON=1
TELLSTICK_TURNOFF=2
TELLSTICK_BELL=4
TELLSTICK_TOGGLE=8
TELLSTICK_DIM=16
TELLSTICK_LEARN=32
TELLSTICK_EXECUTE=64
TELLSTICK_UP=128
TELLSTICK_DOWN=256
TELLSTICK_STOP=512
#Sensor value types
TELLSTICK_TEMPERATURE=1
TELLSTICK_HUMIDITY=2
#Error codes
TELLSTICK_SUCCESS=0
TELLSTICK_ERROR_NOT_FOUND=-1
TELLSTICK_ERROR_PERMISSION_DENIED=-2
TELLSTICK_ERROR_DEVICE_NOT_FOUND=-3
TELLSTICK_ERROR_METHOD_NOT_SUPPORTED=-4
TELLSTICK_ERROR_COMMUNICATION=-5
TELLSTICK_ERROR_CONNECTING_SERVICE=-6
TELLSTICK_ERROR_UNKNOWN_RESPONSE=-7
TELLSTICK_ERROR_UNKNOWN=-99
#Device typedef
TELLSTICK_TYPE_DEVICE=1
TELLSTICK_TYPE_GROUP=2
TELLSTICK_TYPE_SCENE=3
#Device changes
TELLSTICK_DEVICE_ADDED=1
TELLSTICK_DEVICE_CHANGED=2
TELLSTICK_DEVICE_REMOVED=3
TELLSTICK_DEVICE_STATE_CHANGED=4
#Change types
TELLSTICK_CHANGE_NAME=1
TELLSTICK_CHANGE_PROTOCOL=2
TELLSTICK_CHANGE_MODEL=3
TELLSTICK_CHANGE_METHOD=4

# Device methods
TELLDUS_BRIGHT=3
TELLDUS_SHUT=201

deviceEventLock = threading.Lock()
queueLock = threading.Lock()

def sensorEventCallbackFunction(protocol, model, deviceId, dataType, value, timestamp, callbackId, context):
        print "sensorEventCallback: id=%s, method=%s and data=%s" % (deviceId,model,value)

def deviceEventCallbackFunction(deviceId, method, value, callbackId, context):
        if deviceId==0 or method==0 :
            return
        obj = cast(context, py_object).value
        obj.log.debug("deviceEventCallback: id=%s, method=%s and value=%s" % (deviceId,method,value))
        eventDate=datetime.now()
        deviceEventLock.acquire()
        obj._send_xpl(deviceId, method,c_char_p(value).value,callbackId,eventDate)
        deviceEventLock.release()

def deviceChangeEventCallbackFunction(deviceId, changeEvent, changeType, callbackId, context):
        obj = cast(context, py_object).value
        obj.log.debug("deviceChangeEventCallback: id=%s, changeEvent=%s and changeType=%s" % (deviceId,changeEvent,changeType))
        obj._loadDevices()

class deviceEventQueue:
    def __init__(self, delayRF):
        self._delayRF = delayRF
        self._data = dict()

    def addDevice(self, deviceId, method, value, callbackId, eventDate):
        '''
        Add Device to the dictionnary
        '''
        self._data[deviceId] = {'method': method,
                            'value' : value,
                            'callbackId' : callbackId,
                            'eventDate' : eventDate
                            }
        #print deviceId,self._data[deviceId]

    def equal(self, deviceId, method, value, callbackId, eventDate):
        '''
        Add Device to the dictionnary
        '''
        if (deviceId in self._data and self._data[deviceId]['method'] == method and self._data[deviceId]['value'] == value and self._data[deviceId]['callbackId'] == callbackId and (eventDate-self._data[deviceId]['eventDate'] < timedelta(milliseconds=self._delayRF))):
            #print "EQUAL !!!!!!"
            return True
        else:
            #print "NOT EQUAL !!!!!!"
            self.addDevice(deviceId, method, value, callbackId, eventDate)
            return False

class telldusException(Exception):
    """
    telldus exception
    """
    def __init__(self, value):
        Exception.__init__(self)
        self.value = value

    def __str__(self):
        return repr(self.value)

class telldusDevices:

    def __init__(self):
        self._data = dict()

    def addDevice(self, deviceId, name, protocol, model, house, unit, devicetype, param1, param2):
        '''
        Add Device to the dictionnary
        '''
        self._data[deviceId] = {'protocol': protocol,
                            'name' : name,
                            'model' : model,
                            'house' : house,
                            'unit' : unit,
                            'devicetype' : devicetype,
                            'param1' : param1,
                            'param2' : param2,
                            }
        #print deviceId,self._data[deviceId]

    def getId(self, add):
        '''
        Retrieve an id from HU address
        '''
        return int(add[2:])

    def getAddress(self,deviceId):
        '''
        Retrieve an address from deviceId
        '''
        return 'TS'+str(deviceId)

    def getName(self,deviceId):
        '''
        Retrieve an address from deviceId
        '''
        return str(self._data[deviceId]['name'])

    def getDevicetype(self,deviceId):
        '''
        Retrieve a device type deviceId
        '''
        return str(self._data[deviceId]['devicetype'])

    def getDevice(self,deviceId):
        '''
        Retrieve an Device from from deviceId
        @param deviceId : deviceId of the module (given by telldus-core)
        '''
        return self._data[deviceId]

class telldusXPL:
    '''
    Manage the extended XPL language
    ie : shutter -> on, shutter close during 8s(t/2)
    We will scan the incoming messages from the tellstick
    and reassemble them in a complex XPL command
    '''
    def __init__(self,callback):
        self._data = dict()
        self._callback = callback

    def append(self, deviceId, method):
        '''
        Append Device to the dictionnary/list
        '''
        queueLock.acquire()
        if deviceId not in self._data :
            queue=deque()
        else:
            queue=self._data[deviceId]
        queue.append({'deviceId': deviceId,
                            'method' : method,
                            })
        self._data[deviceId]=queue
        #print deviceId,self._data[deviceId]
        queueLock.release()

    def clear(self, deviceId):
        '''
        Clear the queue of the device
        Send an ACK for the complex command.
        '''
        queueLock.acquire()
        if deviceId not in self._data :
            #print False
            queueLock.release()
            return False
        queue = self._data[deviceId]
        ttrue=True
        while ttrue:
            elt = queue.popleft()
            if self.count(deviceId)==0:
                #Yes. This is the complex command
                #We send an XPL message to ack the complex command
                self._callback(elt['deviceId'],elt['method'])
                del self._data[deviceId]
                ttrue=False
        queueLock.release()

    def leftCommand(self, deviceId):
        '''
        Return the left command in the queue
        '''
        queueLock.acquire()
        if deviceId not in self._data :
            #print False
            queueLock.release()
            return 0
        queue = self._data[deviceId]
        elt = queue.popleft()
        queue.appendleft(elt)
        #print "leftCommand : %s" % elt['method']
        queueLock.release()
        return elt['method']

    def inQueue(self, deviceId, method):
        '''
        Validate that the message is a part of a complex XPL message
        '''
        #print deviceId,self._data[deviceId]
        queueLock.acquire()
        if deviceId not in self._data :
            #print False
            queueLock.release()
            return False
        queue = self._data[deviceId]
        elt = queue.popleft()
        if (elt['deviceId']==deviceId) and (elt['method']==method):
            #The message is in the queue. We pop it so we remove it
            #Now we must test if there is only one item in the queue
            if self.count(deviceId)==1:
                #Yes. This is the complex command
                #We send an XPL message to ack the complex command
                elt2 = queue.popleft()
                self._callback(elt2['deviceId'],elt2['method'])
                del self._data[deviceId]
            else:
                #There is many commands in the list ...
                self._data[deviceId]=queue
        else :
            #Well don't know where this message came from
            #we put the message in the queue
            queue.appendleft(elt)
            self._data[deviceId]=queue
        #print True
        queueLock.release()
        return True

    def validate(self, deviceId, method):
        '''
        Validate that the message is not a part of a complex XPL message
        DEPRECATED Use inQueue instead
        '''
        if deviceId not in self._data :
            #print True
            return True
        #print deviceId,self._data[deviceId]
        queue = self._data[deviceId]
        elt = queue.popleft()
        if (elt['deviceId']==deviceId) and (elt['method']==method):
            #The message is in the queue. We pop it so we remove it
            #Now we must test if there is only one item in the queue
            if self.count(deviceId)==1:
                #Yes. This is the complex command
                #We send an XPL message to ack the complex command
                elt2 = queue.popleft()
                self._callback(elt2['deviceId'],elt2['method'])
                del self._data[deviceId]
            else:
                #There is many commands in the list ...
                self._data[deviceId]=queue
        else :
            #Well don't know where this message came from
            #we put the message in the queue
            queue.appendleft(elt)
            self._data[deviceId]=queue
        #print False
        return False

    def count(self, deviceId):
        '''
        Count the number of messages for a device in the queue
        '''
        if deviceId not in self._data :
            #print True
            return 0
        else :
            return len(self._data[deviceId])

class telldusAPI:
    '''
    Telldus python binding library
    '''
    def __init__(self, xplCallback, log, config, XPLSender):
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
        self._xplCallback=xplCallback
        self._tdlib = None
        self.myxpl=XPLSender
        self.log.info("telldusAPI.__init__ : Look for telldus-core")
        ret = ctypes.util.find_library("telldus-core")
        if ret != None:
            try:
                if (platform.system() == 'Windows'):
                    #Windows
                    self._tdlib = windll.LoadLibrary(ret)
                else:
                    #Linux
                    self._tdlib = cdll.LoadLibrary(ret)
            except:
                self.log.exception("telldusAPI.__init__ : Could not load the telldus-core library.")
                raise telldusException("Could not load the telldus-core library.")
                return
        else:
            self.log.error("telldusAPI.__init__ : Could not find the telldus-core library. Check if it is installed properly.")
            raise telldusException("Could not find the telldus-core library. Check if it is installed properly.")
        # Initialize tellDus API
        try:
            self._tdlib.tdInit()
        except:
            self.log.exception("telldusAPI.__init__ : Could not init telldus-core library.")
            raise telldusException("Could not init telldus-core library.")
            return
        self._loadDevices()
        self._loadCommands()
        self._load_telldus_extensions()
        self._lastSentCommand = {}
        if self.config==None:
            self.log.warning("telldusAPI.__init__ : Receiver is disabled.")
        else:
            try:
                self._delayRF = int(self.config.query('telldus', 'delayrf'))
            except:
                self.log.exception("telldusAPI.__init__ : Can't get configuration from XPL")
                self._delayRF = 400
                #print "self=%s" % param
            self.log.debug("telldusAPI.__init__ : Registering the callback functions ...")
            if (platform.system() == 'Windows'):
                CMPFUNC = WINFUNCTYPE(c_void_p, c_int, c_int, c_char_p, c_int, c_void_p)
            else:
               CMPFUNC = CFUNCTYPE(c_void_p, c_int, c_int, c_char_p, c_int, c_void_p)
            self._deviceEventCallback = CMPFUNC(deviceEventCallbackFunction)
            self._deviceEventCallbackId =self._tdlib.tdRegisterDeviceEvent(self._deviceEventCallback, py_object(self))
            self._deviceEventQueue = deviceEventQueue(self._delayRF)
            if (platform.system() == 'Windows'):
                CMPFUNC = WINFUNCTYPE(c_void_p, c_int, c_int, c_int, c_int, c_void_p)
            else:
                CMPFUNC = CFUNCTYPE(c_void_p, c_int, c_int, c_int, c_int, c_void_p)
            self._deviceChangeEventCallback = CMPFUNC(deviceChangeEventCallbackFunction)
            self._deviceChangeEventCallbackId =self._tdlib.tdRegisterDeviceChangeEvent(self._deviceChangeEventCallback, py_object(self))
            self._telldusXPL = telldusXPL(self._call_xplCallback)
        self.log.debug("telldusAPI.__init__ : Done :-)")

    def reloadConfig(self):
        self.log.debug("telldusAPI.reloadConfig : Start")
        if self.config!=None:
            try:
                self._delayRF = int(self.config.query('telldus', 'delayrf'))
            except:
                self.log.exception("telldusAPI.__init__ : Can't get configuration from XPL")
                self._delayRF = 400
        self._loadDevices()
        self.load_tellsdus_extensions()
        self.log.debug("telldusAPI.reloadConfig : Done :-)")

    def _loadDevices(self):
        '''
        Load devices into the _devices dictionnary
        '''
        self.log.debug("telldusAPI._loadDevices : Start ...")
        self._devices = telldusDevices()
        #Read the plugin configurations
        confs= {}
        if self.config!=None :
            num = 1
            loop = True
            while loop == True:
                name = self.config.query('telldus', 'name-%s' % str(num))
                devicetype = self.config.query('telldus', 'devicetype-%s' % str(num))
                param1 = self.config.query('telldus', 'param1-%s' % str(num))
                param2 = self.config.query('telldus', 'param2-%s' % str(num))
                if name != None:
                    self.log.debug("telldusAPI._loadDevices : Configuration from xpl : name=%s, param1=%s, param2=%s" % (name, param1, param2))
                    confs[name] = {"devicetype" : devicetype, "param1" : param1, "param2" : param2}
                else:
                    loop = False
                num += 1
        #Read the devices from telldus-core
        j=0
        for i in range(self._tdlib.tdGetNumberOfDevices()):
            j=j+1
            iid = self._tdlib.tdGetDeviceId(c_int(i))
            #print iid
            id_name = c_char_p(self._tdlib.tdGetName(c_int(iid))).value
            id_house=c_char_p(self._tdlib.tdGetDeviceParameter(c_int(iid), c_char_p("house"), "")).value
            id_unit=c_char_p(self._tdlib.tdGetDeviceParameter(c_int(iid), c_char_p("unit"), "")).value
            id_model = c_char_p(self._tdlib.tdGetModel(c_int(iid))).value.partition(':')[0]
            id_protocol = c_char_p(self._tdlib.tdGetProtocol(c_int(iid))).value
            id_devicetype = None
            id_param1 = None
            id_param2 = None
            if self._devices.getAddress(iid) in confs.iterkeys():
                self.log.debug("telldusAPI._loadDevices : Get configuration from plugin : device=%s" % (self._devices.getAddress(iid)))
                id_devicetype = confs[self._devices.getAddress(iid)]['devicetype']
                id_param1 = confs[self._devices.getAddress(iid)]['param1']
                id_param2 = confs[self._devices.getAddress(iid)]['param2']
            self._devices.addDevice(iid,id_name,id_protocol,id_model,id_house,id_unit,id_devicetype,id_param1,id_param2)
        self.log.debug("telldusAPI._loadDevices : Loading %s devices from telldus-core." % j)
        self.log.debug("telldusAPI._loadDevices : Done :-)")

    def _load_telldus_extensions(self):
        """
        Load the extensions
        """
        if self.config!=None :
            self._load_telldus_windoor()
            self._load_telldus_dawndusk()
            self._load_telldus_move()

    def _load_telldus_windoor(self):
        """
        Load the WINDOOR extension
        """
        self._windoor=None
        boo=self.config.query('telldus', 'windoor')
        if boo==None:
            boo="False"
        self._ext_windoor = eval(boo)
        self.log.debug("telldus.load_telldus_windoor : Load =" + str(type(self._ext_windoor)))
        if self._ext_windoor==True:
            self.log.debug("telldus.load_telldus_windoor : Load windoor extension")
            try:
                self._windoor = telldusWindoorAPI(self)
            except Exception:
                self.log.exception("Something went wrong during windoor extension init, check logs")
        else:
            self.log.debug("telldus.load_telldus_windoor : Don't load windoor extension")

    def _load_telldus_dawndusk(self):
        """
        Load the DAWNDUSK extension
        """
        self._dawndusk=None
        boo=self.config.query('telldus', 'dawndusk')
        if boo==None:
            boo="False"
        self._ext_dawndusk = eval(boo)
        if self._ext_dawndusk==True:
            self.log.debug("telldus.load_telldus_dawndusk : Load dawndusk extension")
            try:
                self._dawndusk = telldusDawnduskAPI(self)
            except Exception:
                self.log.exception("Something went wrong during dawndusk extension init, check logs")
        else:
            self.log.debug("telldus.load_telldus_dawndusk : Don't load dawndusk extension")

    def _load_telldus_move(self):
        """
        Load the MOVE extension
        """
        self._move=None
        boo=self.config.query('telldus', 'move')
        if boo==None:
            boo="False"
        self._ext_move = eval(boo)
        if self._ext_move==True:
            self.log.debug("telldus.load_telldus_move : Load move extension")
            try:
                self._move = telldusMoveAPI(self)
            except Exception:
                self.log.exception("Something went wrong during move extension init, check logs")
        else:
            self.log.debug("telldus.load_telldus_move : Don't load move extension")

    def _loadCommands(self):
        """
        Load commands into a dictionnary
        """
        self.log.debug("telldusAPI._loadCommands : Start ...")
        self._commands = dict()
        if self._tdlib == None:
            self.log.error("Library telldus-core not loaded.")
            raise telldusException("Library telldus-core not loaded.")
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

    def _send_xpl(self,deviceId,method,value,callbackId,eventDate):
        """
        Send messages from Tellstick to xpl
        @param deviceId : the id of the transceiver
        @param method : the command sent
        @param value : the value sent
        @param callbackId : the id of the callback
        @param eventDate : the date of the event. Use to filter redondant events.
        """
        self.log.debug("telldusAPI._send_xpl : Start ...")
        #Try to test the message is not repeated
        if self._deviceEventQueue.equal(deviceId, method, value, callbackId, eventDate)==False:
            #It is not
            #Test if the message is not a part of the complex message
            if self._telldusXPL.inQueue(deviceId, method)==False:
                #print self.isDevicetype(deviceId,self._dawndusk.devicetype)
                self._send_xpl_extensions(deviceId,method,value,callbackId,eventDate)
                self._call_xplCallback(deviceId,method)
        self.log.debug("telldusAPI._send_xpl : Done")

    def _send_xpl_extensions(self,deviceId,method,value,callbackId,eventDate):
        """
        Send messages extensions
        @param deviceId : the id of the transceiver
        @param method : the command sent
        @param value : the value sent
        @param callbackId : the id of the callback
        @param eventDate : the date of the event. Use to filter redondant events.
        """
        self.log.debug("telldusAPI._send_xpl_extensions : Start ...")
        if self._ext_dawndusk==True and self.isDevicetype(deviceId,self._dawndusk.devicetype)==True:
           self.log.debug("telldusAPI._send_xpl : Use the danwdusk extension")
           self._dawndusk.sendDawnDusk(deviceId,method)
        elif self._ext_windoor==True and self.isDevicetype(deviceId,self._windoor.devicetype)==True:
           self.log.debug("telldusAPI._send_xpl : Use the windoor extension")
           self._windoor.sendWindoor(deviceId,method)
        elif self._ext_move==True and self.isDevicetype(deviceId,self._move.devicetype)==True:
           self.log.debug("telldusAPI._send_xpl : Use the move extension")
           self._move.sendMove(deviceId,method)
        self.log.debug("telldusAPI._send_xpl_extensions : Done")

    def _call_xplCallback(self,deviceId,method):
        """
        Call the xplCallback function
        @param deviceId : the id of the transceiver
        @param method : the command sent
        """
        self.log.debug("telldusAPI._call_xplCallback : Start ...")
        self._xplCallback(self._devices.getAddress(deviceId), self._commands[method]['cmd'])
        self.log.debug("telldusAPI._call_xplCallback : Done")

    def __del__(self):
        '''
        Destructor : Cleanup Telldus Lib
        '''
        self.log.debug("telldusAPI.__del__")

    def getDevices(self):
        '''
        Return the collection of the devices
        @return : a the collection of devices
        '''
        return self._devices._data

    def getDevicesFromType(self,devicetype):
        '''
        Return a collection of devices of type devicetype
        @param devicetype : the device type looking for
        @return : a the collection of devices
        '''
        return None

    def isDevicetype(self,deviceId,devicetype):
        '''
        Test if a device is of device type devicetype
        @param deviceid : the id of the device
        @param devicetype : the device type
        @return : True or False
        '''
        return self._devices.getDevicetype(deviceId)==devicetype

    def getDeviceId(self, add):
        '''
        Retrieve an id from HU address
        @param add : address of the module (ie TS14)
        @return : Id of the device
        '''
        return self._devices.getId(add)

    def getDeviceAddress(self,deviceId):
        '''
        Retrieve an address from id
        @param deviceId : id of the module (given by telldus-core)
        '''
        return self._devices.getAddress(deviceId)

    def getDevice(self,deviceId):
        '''
        Retrieve an Device from from id
        @param deviceId : id of the module (given by telldus-core)
        '''
        return self._devices.getDevice(deviceId)

    def getDeviceName(self,deviceId):
        '''
        Retrieve an Device from from id
        @param deviceId : id of the module (given by telldus-core)
        '''
        return self._devices.getDevice(deviceId)['name']

    def printIt(self):
        '''
        Test only method
        '''
        print " telldusAPI print is Ok"

    def sendOn(self, add):
        '''
        Turns the specified device On
        @param add : address of the module (ie TS14)
        '''
        #print " ON : address: %s" % (add)
        self._turnOnDevice(self.getDeviceId(add))

    def sendOff(self, add):
        '''
        Turns the specified device Off
        @param add : address of the module (ie TS14)
        '''
        #print " OFF : address: %s" % (add)
        self._turnOffDevice(self.getDeviceId(add))

    def sendDim(self, add, level):
        '''
        Sets the specified dim level on device
        Level should be between 0 and 255
        @param add : address of the module (ie TS14)
        @param level : level of light (0..255max)
        '''
        if level==0:
            self._turnOffDevice(self.getDeviceId(add))
        elif level==100:
            self._turnOnDevice(self.getDeviceId(add))
        else :
            self._dimDevice(self.getDeviceId(add),int(level))

    def sendBright(self, add, level):
        '''
        Turn on the device and after set the specified dim level on device
        Level should be between 0 and 255
        @param add : address of the module (ie TS14)
        @param level : level of light (0..255max)
        '''
        #print " BRIGHT : address: %s, level: %s" % (add,level)
        deviceId=self.getDeviceId(add)
        self._telldusXPL.append(deviceId,TELLSTICK_TURNON)
        self._telldusXPL.append(deviceId,TELLSTICK_DIM)
        self._telldusXPL.append(deviceId,TELLDUS_BRIGHT)
        self._turnOnDevice(deviceId)
        self._dimDevice(deviceId,int(level))

    def sendBell(self, add):
        '''
        Sends the bell signal to device
        @param add : address of the module (ie TS14)
        '''
        self._bellDevice(self.getDeviceId(add))

    def sendLearn(self, add):
        '''
        Sends the special learn command to device
        @param add : address of the module (ie TS14)
        '''
        self._learnDevice(self.getDeviceId(add))

    def sendUp(self, add):
        '''
        Move the shutter up.
        @param add : address of the module (ie TS14)
        '''
        #print " up : address: %s" % (add)
#        self._upDevice(self.getDeviceId(add))
        deviceId=self.getDeviceId(add)
        if self._deviceMethods(deviceId,TELLSTICK_UP)==TELLSTICK_UP:
            self._upDevice(deviceId)
        elif self._deviceMethods(deviceId,TELLSTICK_TURNON)==TELLSTICK_TURNON:
            dtime=self._devices.getDevice(deviceId)['param1']
            if dtime==None:
                dtime=15
            self._telldusXPL.append(deviceId,TELLSTICK_TURNON)
            self._telldusXPL.append(deviceId,TELLSTICK_TURNON)
            self._telldusXPL.append(deviceId,TELLSTICK_UP)
            self._turnOnDevice(deviceId)
            time.sleep(1.2*int(dtime))
            if self._telldusXPL.count(deviceId)!=0:
                self._turnOnDevice(deviceId)
                self.log.debug("telldusAPI.sendUp continue")
            else:
                self.log.debug("telldusAPI.sendUp cancelled")

    def sendDown(self, add):
        '''
        Move the shutter down.
        @param add : address of the module (ie TS14)
        '''
        #print " down : address: %s" % (add)
#        self._downDevice(self.getDeviceId(add))
        deviceId=self.getDeviceId(add)
        if self._deviceMethods(deviceId,TELLSTICK_DOWN)==TELLSTICK_DOWN:
            self._downDevice(deviceId)
        elif self._deviceMethods(deviceId,TELLSTICK_TURNOFF)==TELLSTICK_TURNOFF:
            dtime=self._devices.getDevice(deviceId)['param1']
            if dtime==None:
                dtime=15
            self._telldusXPL.append(deviceId,TELLSTICK_TURNOFF)
            self._telldusXPL.append(deviceId,TELLSTICK_TURNOFF)
            self._telldusXPL.append(deviceId,TELLSTICK_DOWN)
            self._turnOffDevice(deviceId)
            time.sleep(1.2*int(dtime))
            if self._telldusXPL.count(deviceId)!=0:
                self._turnOffDevice(deviceId)
                self.log.debug("telldusAPI.sendUp continue")
            else:
                self.log.debug("telldusAPI.sendDown cancelled")

    def sendShut(self, add, level):
        '''
        Open the shutter depending on level
        Level should be between 0 and 4
        @param add : address of the module (ie TS14)
        @param level : level of light (0..255max)
        '''
        #print " SHUT : address: %s, level: %s" % (add,level)
        #Shutters don't have the same up and down time
        #Try to correct it ...
        up_start=1.5
        up_factor=1
        down_factor=0.9
        level=3
        deviceId=self.getDeviceId(add)
        dtime=self._devices.getDevice(deviceId)['param1']
        if dtime==None or dtime==0:
            dtime=15
        if level==0:
            self._telldusXPL.append(deviceId,TELLSTICK_TURNOFF)
            self._telldusXPL.append(deviceId,TELLDUS_SHUT)
            self._turnOffDevice(deviceId)
        elif level<3 and level>0:
            self._telldusXPL.append(deviceId,TELLSTICK_TURNOFF)
            self._telldusXPL.append(deviceId,TELLSTICK_TURNON)
            self._telldusXPL.append(deviceId,TELLSTICK_TURNON)
            self._telldusXPL.append(deviceId,TELLDUS_SHUT)
            self._turnOffDevice(deviceId)
            time.sleep(1.2*int(dtime))
            if self._telldusXPL.count(deviceId)!=0:
                self._turnOnDevice(deviceId)
                time.sleep(up_start+int(dtime)*up_factor*level*25/100)
            if self._telldusXPL.count(deviceId)!=0:
                    self._turnOnDevice(deviceId)
        elif level==3:
            self._telldusXPL.append(deviceId,TELLSTICK_TURNON)
            self._telldusXPL.append(deviceId,TELLSTICK_TURNOFF)
            self._telldusXPL.append(deviceId,TELLSTICK_TURNOFF)
            self._telldusXPL.append(deviceId,TELLDUS_SHUT)
            self._turnOnDevice(deviceId)
            time.sleep(1.2*int(dtime))
            if self._telldusXPL.count(deviceId)!=0:
                self._turnOffDevice(deviceId)
                time.sleep(int(dtime)*down_factor*(4-level)*25/100)
            if self._telldusXPL.count(deviceId)!=0:
                self._turnOffDevice(deviceId)
        elif level==4:
            self._telldusXPL.append(deviceId,TELLSTICK_TURNON)
            self._telldusXPL.append(deviceId,TELLDUS_SHUT)
            self._turnOnDevice(deviceId)

#    def sendStop(self, add):
#        '''
#        Stop the shutter.
#        @param add : address of the module (ie TS14)
#        '''
#        #print " stop : address: %s" % (add)
#        deviceId=self.getDeviceId(add)
#        if self._deviceMethods(deviceId,TELLSTICK_DOWN)==TELLSTICK_DOWN:
#            #If the device support the stop method, use it
#            self._stopDevice(deviceId)
#        elif self._deviceMethods(deviceId,TELLSTICK_TURNOFF)==TELLSTICK_TURNOFF \
#           and self._telldusXPL.validate(deviceId, TELLSTICK_TURNOFF):
#              # There is pending action with this method
#              # we remove it, stop the device and send the xpl ack
#              self._turnOffDevice(deviceId)
#              self._call_xplCallback(self,deviceId,TELLSTICK_STOP)
#        elif self._deviceMethods(deviceId,TELLSTICK_TURNON)==TELLSTICK_TURNON \
#           and self._telldusXPL.validate(deviceId, TELLSTICK_TURNON):
#              # There is pending action with this method
#              # we remove it, stop the device and send the xpl ack
#              self._turnOnDevice(deviceId)
#              self._call_xplCallback(self,deviceId,TELLSTICK_STOP)
#        elif self._deviceMethods(deviceId,TELLSTICK_UP)==TELLSTICK_UP \
#           and self._telldusXPL.validate(deviceId, TELLSTICK_UP):
#              # There is pending action with this method
#              # we remove it, stop the device and send the xpl ack
#              self._upDevice(deviceId)
#              self._call_xplCallback(self,deviceId,TELLSTICK_STOP)
#        elif self._deviceMethods(deviceId,TELLSTICK_DOWN)==TELLSTICK_DOWN \
#           and self._telldusXPL.validate(deviceId, TELLSTICK_DOWN):
#              # There is pending action with this method
#              # we remove it, stop the device and send the xpl ack
#              self._downDevice(deviceId)
#              self._call_xplCallback(self,deviceId,TELLSTICK_STOP)

#    def sendStop(self, add):
#        '''
#        Stop the shutter.
#        @param add : address of the module (ie TS14)
#        '''
#        #print " stop : address: %s" % (add)
#        deviceId=self.getDeviceId(add)
#        if self._deviceMethods(deviceId,TELLSTICK_STOP)==TELLSTICK_STOP:
#              #If the device support the stop method, use it
#              print "Last sent = STOP"
#              self._stopDevice(deviceId)
#              return
#        if deviceId in self._lastSentCommand.iterkeys() :
#            if self._lastSentCommand[deviceId]==TELLSTICK_TURNOFF:
#                # There is pending action with this method
#                # we remove it, stop the device and send the xpl ack
#                print "Last sent = TURNOFF"
#                self._turnOffDevice(deviceId)
#                self._call_xplCallback(deviceId,TELLSTICK_STOP)
#            elif self._lastSentCommand[deviceId]==TELLSTICK_TURNON:
#                # There is pending action with this method
#                # we remove it, stop the device and send the xpl ack
#                print "Last sent = TURNON"
#                self._turnOnDevice(deviceId)
#                self._call_xplCallback(deviceId,TELLSTICK_STOP)
#            elif self._lastSentCommand[deviceId]==TELLSTICK_UP:
#                # There is pending action with this method
#                # we remove it, stop the device and send the xpl ack
#                print "Last sent = UP"
#                self._upDevice(deviceId)
#                self._call_xplCallback(deviceId,TELLSTICK_STOP)
#            elif self._lastSentCommand[deviceId]==TELLSTICK_DOWN:
#                # There is pending action with this method
#                # we remove it, stop the device and send the xpl ack
#                print "Last sent = DOWN"
#                self._downDevice(deviceId)
#                self._call_xplCallback(deviceId,TELLSTICK_STOP)

    def sendStop(self, add):
        '''
        Stop the shutter.
        @param add : address of the module (ie TS14)
        '''
        #print " stop : address: %s" % (add)
        deviceId=self.getDeviceId(add)
        if self._deviceMethods(deviceId,TELLSTICK_STOP)==TELLSTICK_STOP:
              #If the device support the stop method, use it
              print "Last sent = STOP"
              self._stopDevice(deviceId)
              return
        #Well. This is a complex method
        if self._telldusXPL.leftCommand(deviceId)==TELLSTICK_TURNOFF:
            # There is pending action with this method
            # we remove it, stop the device and send the xpl ack
            print "Last sent = TURNOFF"
            self._turnOffDevice(deviceId)
            self._telldusXPL.clear(deviceId)
            self._call_xplCallback(deviceId,TELLSTICK_STOP)
        elif self._telldusXPL.leftCommand(deviceId)==TELLSTICK_TURNON:
            # There is pending action with this method
            # we remove it, stop the device and send the xpl ack
            print "Last sent = TURNON"
            self._turnOnDevice(deviceId)
            self._telldusXPL.clear(deviceId)
            self._call_xplCallback(deviceId,TELLSTICK_STOP)
        elif self._telldusXPL.leftCommand(deviceId)==TELLSTICK_UP:
            # There is pending action with this method
            # we remove it, stop the device and send the xpl ack
            print "Last sent = UP"
            self._upDevice(deviceId)
            self._telldusXPL.clear(deviceId)
            self._call_xplCallback(deviceId,TELLSTICK_STOP)
        elif self._telldusXPL.leftCommand(deviceId)==TELLSTICK_DOWN:
            # There is pending action with this method
            # we remove it, stop the device and send the xpl ack
            print "Last sent = DOWN"
            self._downDevice(deviceId)
            self._telldusXPL.clear(deviceId)
            self._call_xplCallback(deviceId,TELLSTICK_STOP)

    def getInfo(self, deviceId):
        '''
        Get the info on the device
        @param deviceId : id of the module
        '''
        if self._tdlib == None:
            self.log.error("Library telldus-core not loaded.")
            raise telldusException("Library telldus-core not loaded.")
        st = []
        st.append("%s : %s" % (deviceId,self._devices.getDevice(deviceId)['name']))
        st.append("model : %s" % (self._devices.getDevice(deviceId)['model']))
        st.append("protocol : %s" % (self._devices.getDevice(deviceId)['protocol']))
        st.append("house : %s / unit: %s" % (self._devices.getDevice(deviceId)['house'],self._devices.getDevice(deviceId)['unit']))
        st.append("Methods :")
        s1,s2,s3="No","No","No"
        if self._deviceMethods(deviceId,TELLSTICK_TURNON)==TELLSTICK_TURNON:
            s1="Yes"
        if self._deviceMethods(deviceId,TELLSTICK_TURNOFF)==TELLSTICK_TURNOFF:
            s2="Yes"
        if self._deviceMethods(deviceId,TELLSTICK_DIM)==TELLSTICK_DIM:
            s3="Yes"
        st.append("ON : %s / OFF: %s / DIM: %s" % (s1,s2,s3))
        s1,s2,s3,s4="No","No","No","No"
        if self._deviceMethods(deviceId,TELLSTICK_BELL)==TELLSTICK_BELL:
            s1="Yes"
        if self._deviceMethods(deviceId,TELLSTICK_TOGGLE)==TELLSTICK_TOGGLE:
            s2="Yes"
        if self._deviceMethods(deviceId,TELLSTICK_LEARN)==TELLSTICK_LEARN:
            s3="Yes"
        if self._deviceMethods(deviceId,TELLSTICK_EXECUTE)==TELLSTICK_EXECUTE:
            s4="Yes"
        st.append("BELL : %s / TOGGLE: %s / LEARN: %s / EXECUTE: %s" % (s1,s2,s3,s4))
        s1,s2,s3="No","No","No"
        if self._deviceMethods(deviceId,TELLSTICK_UP)==TELLSTICK_UP:
            s1="Yes"
        if self._deviceMethods(deviceId,TELLSTICK_DOWN)==TELLSTICK_DOWN:
            s2="Yes"
        if self._deviceMethods(deviceId,TELLSTICK_STOP)==TELLSTICK_STOP:
            s3="Yes"
        st.append("UP : %s / DOWN: %s / STOP: %s" % (s1,s2,s3))
        return st

    def _turnOnDevice(self,deviceId):
        '''
        Turns the internal device On
        @param deviceId : id of the module
        '''
        self._lastSentCommand[deviceId]=TELLSTICK_TURNON
        self._tdlib.tdTurnOn(c_int(deviceId))

    def _turnOffDevice(self,deviceId):
        '''
        Turns the internal device Off
        @param deviceId : id of the module
        '''
        self._lastSentCommand[deviceId]=TELLSTICK_TURNOFF
        self._tdlib.tdTurnOff(c_int(deviceId))

    def _bellDevice(self,deviceId):
        '''
        Bells the device
        @param deviceId : id of the module
        '''
        self._lastSentCommand[deviceId]=TELLSTICK_BELL
        self._tdlib.tdBell(c_int(deviceId))

    def _learnDevice(self,deviceId):
        '''
        Sends a special Learn command to the device
        @param deviceId : id of the module
        '''
        self._lastSentCommand[deviceId]=TELLSTICK_LEARN
        self._tdlib.tdLearn(c_int(deviceId))

    def _dimDevice(self, deviceId, level):
        '''
        Dims the device level should be between 0 and 100
        tdlib use a level from 0 to 255. So we translate it.
        @param deviceId : id of the module
        @param level : level of light (0..100)
        '''
        #print " DIM : device: %s, level: %s / %s" % (deviceId,level,type(level))
        if level >= 0 and level <= 100:
            self._lastSentCommand[deviceId]=TELLSTICK_DIM
            self._tdlib.tdDim(c_int(deviceId), c_ubyte(int(level*2.55)))

    def _upDevice(self,deviceId):
        '''
        Move the shutter up.
        Test if the device support the up command
        If not try to send an on command
        @param deviceId : id of the module
        '''
        self._lastSentCommand[deviceId]=TELLSTICK_UP
        self._tdlib.tdUp(c_int(deviceId))

    def _downDevice(self,deviceId):
        '''
        Move the shutter down.
        Test if the device support the up command
        If not try to send an on command
        @param deviceId : id of the module
        '''
        self._lastSentCommand[deviceId]=TELLSTICK_DOWN
        self._tdlib.tdDown(c_int(deviceId))

    def _stopDevice(self,deviceId):
        '''
        Stop the shutter.
        Test if the device support the up command
        If not try to manage it supporting the on command
        @param deviceId : id of the module
        '''
        self._lastSentCommand[deviceId]=TELLSTICK_STOP
        self._tdlib.tdStop(c_int(deviceId))

    def _deviceMethods(self,deviceId,methods):
        '''
        Stop the shutter.
        Test if the device support the up command
        If not try to manage it supporting the on command
        @param deviceId : id of the module
        '''
        #int methods = tdMethods(id, TELLSTICK_TURNON | TELLSTICK_TURNOFF | TELLSTICK_BELL);
        return self._tdlib.tdMethods(c_int(deviceId),methods)

if __name__ == "__main__":
    print("TellStick Python binding Class")
    print("Testing mode.\n")
    print("..Creating TellStick object")
    tell = telldusAPI()
    print("..OK")
    print("..Sending a ON command")
    #tell.sendOn("arctech", "selflearning-switch", "0x12345", "2")
    tell.sendOn(3)
    print("..OK")
    print("..Sending a OFF command")
    #tell.sendOff("arctech", "selflearning-switch", "0x12345", "3")
    tell.sendOff(3)
    print("..OK")
    print("\nAll is OK")
