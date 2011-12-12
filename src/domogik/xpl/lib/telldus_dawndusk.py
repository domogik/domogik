#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
This is the dawndusk extention to the telldus plugin
It allows to use obscurity detector to send xpl dawndusk messages
over the XPL network
Example usage :
 ts = telldusDawnduskAPI()
Prototypes :

@author: Sebastien GALLET <sgallet@gmail.com>
@license: GPL(v3)
"""
from domogik.xpl.common.xplconnector import Listener
from domogik.xpl.common.xplmessage import XplMessage
from domogik.xpl.common.plugin import XplPlugin
from domogik.xpl.common.queryconfig import Query

TELLDUS_UNKNOWN=0
TELLDUS_ON=1
TELLDUS_OFF=2

class telldusDawnduskAPI:
    '''
    Dawndusk extension to telldus pugin
    '''
    def __init__(self, plugin):
        '''
        Constructor : Find telldus-core library and try to open it
        If success : initialize telldus API
        @param xplCallback : method of the plug in to send xpl messages
        @param log : a logger
        @param config : the plugin configurator to use. None to disable
        the receiver.
        '''
        self._plugin = plugin
        self._plugin.log.debug("telldusDawnduskAPI.__init__ : Start ...")
        self.devicetype="DAWNDUSK"
        self._state=TELLDUS_UNKNOWN

        #Create listeners
        self._plugin.log.debug("telldusDawnduskAPI.__init__ : Create listeners")
        Listener(self.dawndusk_cmnd_cb, self._plugin.myxpl,
                 {'schema': 'dawndusk.request', 'xpltype': 'xpl-cmnd'})
        self._plugin.log.debug("telldusDawnduskAPI.__init__ : Done :-)")

    def dawndusk_cmnd_cb(self, message):
        """
        General callback for all command messages
        @param message : an XplMessage object
        """
        self._plugin.log.debug("telldusDawnduskAPI.dawndusk_cmnd_cb() : Start ...")
        cmd = None
        if 'command' in message.data:
            cmd = message.data['command']
        query = None
        if 'query' in message.data:
            query = message.data['query']
        self._plugin.log.debug("telldusDawnduskAPI.dawndusk_cmnd_cb :  command %s received with query %s" %
                       (cmd,query))
        mess = XplMessage()
        mess.set_type("xpl-stat")
        sendit=False
        if cmd=="status":
            if query=="daynight":
                mess.set_schema("dawndusk.basic")
                mess.add_data({"type" : "daynight"})
                if self._state==TELLDUS_UNKNOWN:
                    mess.add_data({"status" :  "unknown"})
                    sendit=True
                    self._plugin.log.debug("telldusDawnduskAPI.dawndusk_cmnd_cb() : send message with status= unknown")
                elif self._state==TELLDUS_ON:
                    mess.add_data({"status" :  "night"})
                    sendit=True
                    self._plugin.log.debug("telldusDawnduskAPI.dawndusk_cmnd_cb() : send message with status= night")
                elif self._state==TELLDUS_OFF:
                    mess.add_data({"status" :  "day"})
                    sendit=True
                    self._plugin.log.debug("telldusDawnduskAPI.dawndusk_cmnd_cb() : send message with status= day")
        if sendit:
            self._plugin.myxpl.send(mess)
        self._plugin.log.debug("telldusDawnduskAPI.dawndusk_cmnd_cb() : Done :)")

    def sendDawnDusk(self,deviceid,state):
        """
        Send a xPL message of the type DAWNDUSK.BASIC when the sun goes down or up
        @param state : DAWN or DUSK
        """
        self._plugin.log.debug("telldusDawnduskAPI.sendDawnDusk() : Start ...")
        self._state=state
        mess = XplMessage()
        mess.set_type("xpl-trig")
        mess.set_schema("dawndusk.basic")
        mess.add_data({"type" : "dawndusk"})
        sendit=False
        if state==TELLDUS_OFF:
            mess.add_data({"status" :  "dawn"})
            self._plugin.log.info("telldusDawnduskAPI : Send dawndusk message over XPL with status= %s" % "dawn")
            sendit=True
        elif state==TELLDUS_ON:
            mess.add_data({"status" :  "dusk"})
            self._plugin.log.info("telldusDawnduskAPI : Send dawndusk message over XPL with status= %s" % "dusk")
            sendit=True
        if sendit:
            self._plugin.myxpl.send(mess)
        self._plugin.log.debug("telldusDawnduskAPI.sendDawnDusk() : Done :-)")

if __name__ == "__main__":
    print("TellStick Python binding Class")
    print("Testing mode.\n")
    print("..Creating TellStick object")
    tell = telldusDawnduskAPI()
    print("..OK")
    print("..Sending a ON command")
    #tell.sendOn("arctech", "selflearning-switch", "0x12345", "2")
    #tell.sendOn(3)
    print("..OK")
    print("..Sending a OFF command")
    #tell.sendOff("arctech", "selflearning-switch", "0x12345", "3")
    #tell.sendOff(3)
    print("..OK")
    print("\nAll is OK")
