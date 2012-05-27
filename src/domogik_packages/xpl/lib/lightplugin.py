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
Extension to the XplPlugin to add lighting support.
This support may also be available for external (like arduino using a special lib)

Implements
==========
class pluginHelper
class XplHlpPlugin(XplPlugin)
    def enable_helper(self)
"""

from domogik.xpl.common.xplconnector import Listener
from domogik.xpl.common.xplmessage import XplMessage
import traceback
import time

class LightingExtension():
    """
    Add support for lighting to plugin
    """
    def __init__(self, plugin, name, cb_activate_device, cb_deactivate_device,
        cb_valid_device):
        """
        """
        self._plugin = plugin
        self._name = name
        #The list of devices using the lighting shema
        #A device is identified by the fields : device, channel
        #The value is the list of scene parameters
        #ie : _devices["TS35"]["-1"]["scn1"] = {"level":100, "faderate":0}
        self._scenes = {}
        #The lighting extension is started
        self._started = False
        #The lighting extension is started and confgured
        self._active = False
        #The callbaks methods
        self.cb_activate_device = cb_activate_device
        self.cb_deactivate_device = cb_deactivate_device
        self.cb_valid_device = cb_valid_device
        #The listeners
        self._listeners = []

    def enable_lighting(self):
        """
        Enable the lighting listeners
        @param name : the name of the client
        @param cb_activate_device : the callback method to activate a device
        @param cb_deactivate_device : the callback method to deactivate a device
        @param cb_valid_device : the callback method to validate a device

        """
        if self._started == True or self.cb_activate_device == None \
          or self.cb_deactivate_device == None or self.cb_valid_device == None :
            return False
        else :
            continu = True
            if self._started == False and continu == True:
                try :
                    #print "load configuration"
                    self._listeners.append( Listener(self.activate_cmnd_listener, self._plugin.myxpl,
                        {'schema': 'lighting.basic', 'xpltype': 'xpl-cmnd', 'command': 'activate'}))
                    self._listeners.append( Listener(self.deactivate_cmnd_listener, self._plugin.myxpl,
                        {'schema': 'lighting.basic', 'xpltype': 'xpl-cmnd', 'command': 'deactivate'}))
            #       Listener(self.basic_cmnd_listener, self._plugin.myxpl,
            #           {'schema': 'lighting.basic', 'xpltype': 'xpl-cmnd'})
                    self._listeners.append( Listener(self.config_stat_listener, self._plugin.myxpl,
                        {'schema': 'lighting.config', 'xpltype': 'xpl-stat'}))
                    self._listeners.append( Listener(self.config_trig_listener, self._plugin.myxpl,
                        {'schema': 'lighting.config', 'xpltype': 'xpl-trig'}))
                    self._started = True
                except :
                    error = "Exception : %s" % (traceback.format_exc())
                    self._plugin.log.error("LightingExtension.enable_lighting \: " + error)
                    continu = False
            if self._started == True and continu == True:
                try :
                    #request the configuration from the lighting gateway.
                    #print "load configuration"
                    self.load_configuration()
                    continu = True
                except :
                    error = "Exception : %s" % (traceback.format_exc())
                    self._plugin.log.error("LightingExtension.enable_lighting \: " + error)
                    continu = False
            return continu

    def stop_lighting(self, cb_activate_device, cb_deactivate_device,
        cb_valid_device):
        """
        Enable the lighting listeners
        @param name : the name of the client
        @param cb_activate_device : the callback method to activate a device
        @param cb_deactivate_device : the callback method to deactivate a device
        @param cb_valid_device : the callback method to validate a device

        """
        for lis in self._liteners:
            del(lis)

    def add_device(self, scene, device, channel, level, faderate):
        """
        Add a device to scene
        """
        if scene not in self._scenes :
            self._scenes[scene] = {}
        if device not in self._scenes[scene] :
            self._scenes[scene][device] = {}
        if channel not in self._scenes[scene][device] :
            self._scenes[scene][device][channel] = {"level" : level,
                                                    "faderate" : faderate}

    def del_scene(self, scene):
        """
        Delete a scene
        """
        if scene in self._scenes :
            del(self._scenes[scene])

    def valid_device(self, device, channel):
        """
        Encapsulate the callback function
        """
        #print "validate a device"
        return self.cb_valid_device(device, channel)

    def activate_device(self, device, channel, level, faderate):
        """
        Encapsulate the callback function
        """
        return self.cb_activate_device(device, channel, level, faderate)

    def deactivate_device(self, device, channel, level, faderate):
        """
        Encapsulate the callback function
        """
        return self.cb_deactivate_device(device, channel, level, faderate)

    def valid_scene(self, scene):
        """
        Is the scene managed by this plugin
        """
        return scene != None and scene in self._scenes

    def load_configuration(self):
        """
        Load scenes configuration fron gateways
        """
        #print "load configuration"
        mess = XplMessage()
        mess.set_type("xpl-cmnd")
        mess.set_schema("lighting.config")
        mess.add_data({"client" : self._name})
        mess.add_data({"command" : "scnlist"})
        self._plugin.myxpl.send(mess)
        return True

    def basic_cmnd_listener(self, message):
        """
        Listen to lighting.basic messages
        @param message : The XPL message
        @param myxpl : The XPL sender
        """
        commands = {
            'activate': lambda x,m,s: self.cmd_activate(x, m, s),
            'deactivate': lambda x,m,s: self.cmd_deactivate(x, m, s),
#            'on': lambda x,m,s: self.cmd_on(x, m),
#            'off': lambda x,m,s: self.cmd_off(x, m),
#            'dim': lambda x,m,S: self.cmd_dim(x, m),
        }
        try:
            scene = None
            if 'scene' in message.data:
                scene = message.data['scene']
            if self.valid_scene(scene):
                command = None
                if 'command' in message.data:
                    command = message.data['command']
                commands[command](self._plugin.myxpl, message, scene)
            else :
                self._plugin.log.debug("LightingExtension.basic_cmnd_listener \
: not a valid scene")
        except:
            error = "Exception : %s" % (traceback.format_exc())
            self._plugin.log.error("LightingExtension.basic_cmnd_listener \
: " + error)

    def activate_cmnd_listener(self, message):
        """
        Listen to lighting.basic messages
        @param message : The XPL message
        @param myxpl : The XPL sender
        """
        try:
            scene = None
            if 'scene' in message.data:
                scene = message.data['scene']
            if self.valid_scene(scene):
                self.cmd_activate(self._plugin.myxpl, message, scene)
            else :
                self._plugin.log.debug("LightingExtension.activate_cmnd_listener : not a valid scene")
        except:
            error = "Exception : %s" % (traceback.format_exc())
            self._plugin.log.error("LightingExtension.activate_cmnd_listener : " + error)

    def deactivate_cmnd_listener(self, message):
        """
        Listen to lighting.basic messages
        @param message : The XPL message
        @param myxpl : The XPL sender
        """
        try:
            scene = None
            if 'scene' in message.data:
                scene = message.data['scene']
            if self.valid_scene(scene):
                self.cmd_deactivate(self._plugin.myxpl, message, scene)
            else :
                self._plugin.log.debug("LightingExtension.deactivate_cmnd_listener : not a valid scene")
        except:
            error = "Exception : %s" % (traceback.format_exc())
            self._plugin.log.error("LightingExtension.deactivate_cmnd_listener : " + error)

    def config_stat_listener(self, message):
        """
        Listen to lighting.basic messages
        @param message : The XPL message
        @param myxpl : The XPL sender
        """
        configs = {
            'scninfo': lambda x,m: self.stat_scninfo(x, m),
            'scnlist': lambda x,m: self.stat_scnlist(x, m),
        }
        try:
            command = None
            if 'command' in message.data:
                command = message.data['command']
            client = None
            if 'client' in message.data:
                client = message.data['client']
            if client == self._name:
                configs[command](self._plugin.myxpl, message)
        except:
            error = "Exception : %s" % (traceback.format_exc())
            self._plugin.log.error("LightingExtension.config_stat_listener : " + error)

    def config_trig_listener(self, message):
        """
        Listen to lighting.config messages.
        This message is received when the configuration is updated on gateway.
        @param message : The XPL message
        @param myxpl : The XPL sender
        """
        badcommands = ['gateinfo', 'scnlist', 'scnadd', 'scndel', \
             'scnadddev', 'scndeldev' ]
        configs = {
            'scninfo': lambda x,m: self.stat_scninfo(x, m),
        }
        try:
            command = None
            if 'command' in message.data:
                command = message.data['command']
            if command not in badcommands :
                configs[command](self._plugin.myxpl, message)
        except:
            error = "Exception : %s" % (traceback.format_exc())
            self._plugin.log.error("LightingExtension.config_trig_listener \
: " + error)

    def cmd_activate(self, myxpl, message, scene):
        """
        @param myxpl : The XPL sender
        @param message : The XPL message
        @param scene : the scene name
        """
        mess = XplMessage()
        mess.set_type("xpl-trig")
        mess.set_schema("lighting.basic")
        mess.add_data({"command" : "activate"})
        mess.add_data({"scene" : scene})
        mess.add_data({"client" : self._name})
        for device in self._scenes[scene] :
            for channel in self._scenes[scene][device] :
                self.activate_device(device, channel,
                    self._scenes[scene][device][channel]["level"],
                    self._scenes[scene][device][channel]["faderate"])
        myxpl.send(mess)

    def cmd_deactivate(self, myxpl, message, scene):
        """
        @param myxpl : The XPL sender
        @param message : The XPL message
        @param scene : the scene name
        """
        mess = XplMessage()
        mess.set_type("xpl-trig")
        mess.set_schema("lighting.basic")
        mess.add_data({"command" : "deactivate"})
        mess.add_data({"scene" : scene})
        mess.add_data({"client" : self._name})
        for device in self._scenes[scene] :
            for channel in self._scenes[scene][device] :
                self.deactivate_device(device, channel,
                    self._scenes[scene][device][channel]["level"],
                    self._scenes[scene][device][channel]["faderate"])
        myxpl.send(mess)

    def stat_scnlist(self, myxpl, message):
        """
        @param myxpl : The XPL sender
        @param message : The XPL message
        """
        scenes = None
        if 'scenes' in message.data:
            scenes = message.data['scenes']
        if scenes == None:
            self._plugin.log.warning("LightingExtension.stat_scnlist : can't retrieve scenes from lighting gateway.")
        else:
            for scene in scenes.split(","):
                mess = XplMessage()
                mess.set_type("xpl-cmnd")
                mess.set_schema("lighting.config")
                mess.add_data({"client" : self._name})
                mess.add_data({"command" : "scninfo"})
                mess.add_data({"scene" : scene})
                myxpl.send(mess)
                #time.sleep(1)

    def stat_scninfo(self, myxpl, message):
        """
        @param myxpl : The XPL sender
        @param message : The XPL message
        """
        scene = None
        #print "message = %s" % message
        if 'scene' in message.data:
            scene = message.data['scene']
        if scene == None:
            self._plugin.log.warning("LightingExtension.stat_scninfo : can't retrieve scene name from message.")
        else:
            self.del_scene(scene)
            if "device" in message.data:
                if type(message.data['device']) == type(""):
                    start, separator, end = str(message.data['device']).partition(",")
                    ddevice = start
                    #print "ddevice=%s" % ddevice
                    start, separator, end = end.partition(",")
                    dchannel = start
                    #print "dchannel=%s" % dchannel
                    start, separator, end = end.partition(",")
                    dlevel = start
                    #print "dlevel=%s" % dlevel
                    start, separator, end = end.partition(",")
                    dfaderate = start
                    #print "dfaderate=%s" % dfaderate
                    if self.valid_device(ddevice, dchannel):
                        self.add_device(scene, ddevice, dchannel, dlevel, dfaderate)
                else :
                    for device in message.data['device']:
                        #print "device=%s" % device
                        start, separator, end = str(device).partition(",")
                        ddevice = start
                        #print "ddevice=%s" % ddevice
                        start, separator, end = end.partition(",")
                        dchannel = start
                        #print "dchannel=%s" % dchannel
                        start, separator, end = end.partition(",")
                        dlevel = start
                        #print "dlevel=%s" % dlevel
                        start, separator, end = end.partition(",")
                        dfaderate = start
                        #print "dfaderate=%s" % dfaderate
                        if self.valid_device(ddevice, dchannel):
                            self.add_device(scene, ddevice, dchannel, dlevel, dfaderate)
        #print "scenes = %s" % (self._scenes)
