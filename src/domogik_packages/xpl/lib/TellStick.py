#
# This is a Python binding library for TellStick RF transciever.
# It allows you to control several RF home automation device using
# protocols on 433.92 Mhz band such as Chacon, HomeEasy, ...
#
# It requires the telldus-core library is installed on your system.
#
# Warning : The user you run your program under must :
# - Have access to USB subsystem (for example on ubuntu your user
# should be in the plugdev group.
# - Have read AND write access to /etc/tellstick.conf file : this
# is a requirement of the libtelldus-core C library
#
# Example usage :
#  ts = TellStick()
#  ts.setOn("arctech", "selflearning-switch", "0x12345", "2")
# Prototypes :
#  sendOn(protocol, model, house, unit)
#  sendOff(protocol, model, house, unit)
#  sendDim(protocol, model, house, unit, level)
#  sendLearn(protocol, model, house, unit)
#  sendBell(protocol, model, house, unit)
#
# For a list of supported protocols/models, please see the
# telldus-core documentation :
#  http://developer.telldus.se/wiki/TellStick_conf
#
# References :
# - Library telldus-core installation instructions :
#  http://developer.telldus.se/wiki/TellStick_installation_Linux
# - Telldus website (company building the TellStick and author
# of the telldus-core C library)
#  http://www.telldus.se
#
# Author : Thibault Lamy <titi@poulpy.com>
# - http://www.poulpy.com
#

import ctypes
from ctypes import *
from ctypes.util import find_library

class TellStick:
    '''
    TellStick python binding library
    '''
    def __init__(self):
        '''
        Constructor : Find telldus-core library and try to open it
        If success : initialize telldus API
        '''
        self._devid = -1
        self._tdlib = None
        ret = ctypes.util.find_library("telldus-core")
        if ret != None:
            try:
                self._tdlib = cdll.LoadLibrary(ret)
            except:
                print("Could not load the telldus-core library")
                raise Exception("Could not load the telldus-core library")
                return
        else:
            raise Exception("Could not find the telldus-core library. Check if it is installed properly.")
        # Initialize tellDus API
        self._tdlib.tdInit()
        # add Internal Device
        self._addMyDevice()

    def _addMyDevice(self):
        '''
        Add internal device
        '''
        if self._tdlib == None:
            raise Exception("Library not loaded")
        try:
            self._devid = c_int(self._tdlib.tdAddDevice()).value
        except e:
            raise Exception('Could not create device')
        #if (self._devid <= 0):
        #    raise Exception('Could not create device')
        self._tdlib.tdSetName(c_int(self._devid), c_char_p('PythonLib-DEV'))

    def _delMyDevice(self):
        '''
        Delete internal device
        '''
        if self._tdlib == None:
            raise Exception("Library not loaded")
        if self._devid > 0:
            self._tdlib.tdRemoveDevice(c_int(self._devid))

    def __del__(self):
        '''
        Destructor : Cleanup Telldus Lib
        '''
        if self._tdlib != None:
            self._delMyDevice()
            self._tdlib.tdClose()

    def sendOn(self, protocol, model, house, unit):
        '''
        Turns the specified device On
        '''
        self._setupDevice(protocol, model, house, unit)
        self._turnOnDevice()

    def sendOff(self, protocol, model, house, unit):
        '''
        Turns the specified device Off
        '''
        self._setupDevice(protocol, model, house, unit)
        self._turnOffDevice()

    def sendDim(self, protocol, model, house, unit, level):
        '''
        Sets the specified dim level on device
        Level should be between 0 and 255
        '''
        self._setupDevice(protocol, model, house, unit)
        self._dimDevice(level)

    def sendBell(self, protocol, model, house, unit):
        '''
        Sends the bell signal to device
        '''
        self._setupDevice(protocol, model, house, unit)
        self._bellDevice()

    def sendLearn(self, protocol, model, house, unit):
        '''
        Sends the special learn command to device
        '''
        self._setupDevice(protocol, model, house, unit)
        self._learnDevice()

    def _setupDevice(self, protocol, model, house, unit):
        '''
        Sets the device settings and parameters (protocol, model, and address)
        '''
        if self._tdlib == None:
            raise Exception("Library not loaded")
        if self._devid <= 0:
            raise Exception('Device not initialized')
        self._tdlib.tdSetProtocol(c_int(self._devid), c_char_p(protocol))
        self._tdlib.tdSetModel(c_int(self._devid), c_char_p(model))
        if (protocol.lower() == "arctech" and model.lower() == "selflearning-switch"):
            # Fixup some 0-indexation problems and conversions
            unit = str(int(unit) + 1)
            # Convert fomr hexa to int if needed
            if (house[0:2].lower() == "0x"):
                intval = int(house[2:], 16)
                house = str(intval)
        self._tdlib.tdSetDeviceParameter(c_int(self._devid), c_char_p("house"), c_char_p(house))
        self._tdlib.tdSetDeviceParameter(c_int(self._devid), c_char_p("unit"), c_char_p(unit))

    def _turnOnDevice(self):
        '''
        Turns the internal device On
        '''
        self._tdlib.tdTurnOn(c_int(self._devid))

    def _turnOffDevice(self):
        '''
        Turns the internal device Off
        '''
        self._tdlib.tdTurnOff(c_int(self._devid))

    def _bellDevice(self):
        '''
        Bells the device
        '''
        self._tdlib.tdBell(c_int(self._devid))

    def _learnDevice(self):
        '''
        Sends a special Learn command to the device
        '''
        self._tdlib.tdLearn(c_int(self._devid))

    def _dimDevice(self, level):
        '''
        Dims the device level should be between 0 and 255
        '''
        if level >= 0 and level <= 255:
            self._tdlib.tdDim(c_int(self._devid), c_short(level))


if __name__ == "__main__":
    print("TellStick Python binding Class")
    print("Testing mode.\n")
    print("..Creating TellStick object")
    tell = TellStick()
    print("..OK")
    print("..Sending a ON command")
    tell.sendOn("arctech", "selflearning-switch", "0x12345", "2")
    print("..OK")
    print("..Sending a OFF command")
    tell.sendOff("arctech", "selflearning-switch", "0x12345", "3")
    print("..OK")
    print("\nAll is OK")
