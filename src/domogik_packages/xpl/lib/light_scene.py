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

Handle the scene notion in XPL :


Implements
==========

@author: Sébastien Gallet <sgallet@gmail.com>
@copyright: (C) 2007-2009 Domogik project
@license: GPL(v3)
@organization: Domogik
"""
import ConfigParser
import os
import glob
from domogik.xpl.common.xplmessage import XplMessage
#import traceback

class LightingScene():
    """
    Scene

    A scene is a single identifier that when used, can command an
    arbitrarily defined group of lighting devices to change themselves
    to a new level. Most switches/devices that support scenes can be
    associated with more than one scene and for each scene, the switch
    typically has a unique "dim-level" that it will goto when that
    scene is requested (activated, in the lighting schema parlance).
    In some protocols, scenes are known as links. Each Scene has an
    ID that is unique within a Network.
    Provides details information about a specific scene

     network=ID
     scene=ID
     status=[ok|not-found]
     name=[scene name, if known]
     device-count=#
     device=deviceid,channel,level,fade-rate

    network=ID
    Network ID the scninfo request was made for
    scene=ID
    Scene ID the scninfo request was made for
    status=[ok|not-found]
    If the network ID or Scene ID in the originating request were
    invalid or unknown, not-found is returned. If the network ID and
    scene ID were OK, ok is returned. There may be other values
    introduced in the future, so assume "ok" is success and
    anything else is failure.
    name=
    Name of the scene. This should be succinct, describe its "activated"
    state (i.e. "Early Morning Lights") and be presentable and
    understandable by an end user.
    device-count=#
    Number of devices associated with this scene. This can be any
    number from 0 up.
    device=deviceid,channel,level,faderate
    There is one entry for each device associated with this scene.
    Each entry describes the device, channel, level and fade rate that
    a device would go to when the scene is activated.
    deviceid - ID of a device associated with this scene
    channel - channel within that device this scene acts on
    (or 0 for all channels)
    level - level devices channel should go to when scene is activated.
    This will be a value from 0 to 100, "default" or "last".
    fade-rate - fade rate of change to new level in seconds or "default"
    to use the devices default fade rate for each channel.
    """

    def __init__(self, gateway, data_dir):
        self._gateway = gateway
        self._store = LightingSceneStore(self._gateway.log, data_dir)
        self._scenes = {}
        self._store.load_all(self.new, self.add_device)
        self.fields = ["name", "room", "floor", "comment"]
        for scene in self._scenes:
            self.trig_scninfo(scene)
#        self.new("cuiamb", name="Ambiance", room="Cuisine")
#        self.add_device("cuiamb", "TS26")
#        self.add_device("cuiamb", "TS30")
#        self.new("cuiall", name="Toutes", room="Cuisine")
#        self.add_device("cuiall", "TS2")
#        self.add_device("cuiall", "TS21")
#        self.add_device("cuiall", "TS25")
#        self.add_device("cuiall", "TS26")
#        self.add_device("cuiall", "TS27")
#        self.add_device("cuiall", "TS28")
#        self.add_device("cuiall", "TS29")
#        self.add_device("cuiall", "TS30")
#        self.new("samtv", name="TV Scene", room="Salle à manger")
#        self.add_device("samtv", "TS34", level="0")
#        self.add_device("samtv", "TS17", level="20")
#        self.add_device("samtv", "TS35", level="20")
#        self.add_device("samtv", "ARRGB1", channel=1, level="11")
#        self.add_device("samtv", "ARRGB1", channel=2, level="22")
#        self.add_device("samtv", "ARRGB1", channel=3, level="33")
#        self.new("samoff", name="Off Scene", room="Salle à manger")
#        self.add_device("samoff", "TS34", level="0")
#        self.add_device("samoff", "TS17", level="0")
#        self.add_device("samoff", "TS35", level="0")
#        self.add_device("samoff", "ARRGB1", channel=1, level="0")
#        self.add_device("samoff", "ARRGB1", channel=2, level="0")
#        self.add_device("samoff", "ARRGB1", channel=3, level="0")
#        self.new("samon", name="On Scene", room="Salle à manger")
#        self.add_device("samon", "TS34", level="100")
#        self.add_device("samon", "TS17", level="100")
#        self.add_device("samon", "TS35", level="100")
#        self.add_device("samon", "ARRGB1", channel=1, level="100")
#        self.add_device("samon", "ARRGB1", channel=2, level="100")
#        self.add_device("samon", "ARRGB1", channel=3, level="100")
#        self.new("chsex", name="Sex Scene", room="Chambre")
#        self.add_device("chsex", "TS5", level=10)
#        self.add_device("chsex", "TS31", level=0)
#        self.new("chtv", name="TV Scene", room="Chambre")
#        self.add_device("chtv", "TS5", level=20)
#        self.add_device("chtv", "TS31", level=0)
#        self.new("choff", name="Off Scene", room="Chambre")
#        self.add_device("choff", "TS32", level=0)
#        self.add_device("choff", "TS31", level=0)
#        self.new("chon", name="On Scene", room="Chambre")
#        self.add_device("chon", "TS32", level=100)
#        self.add_device("chon", "TS31", level=100)
        print "scenes"
        for scene in self._scenes:
            print self._scenes[scene]

    def _new(self, scene, name="unknown", status="not-found",
             room=None, floor=None, comment=None):
        """
        Create a new scene. Internal method.
        """
        ok = True
        self._scenes[scene] = {
            "name" : name,
            "status" : status,
            "room" : room,
            "floor" : floor,
            "comment" : comment,
            "devices" : {}
            }
        return ok

    def _remove(self, scene):
        """
        Delete a scene. Internal method.
        """
        ok = True
        del(self._scenes[scene])
        return ok

    def new(self, scene, name="unknown", status="ok", room=None,
             floor=None, comment=None):
        """
        Create a new scene.
        """
        if not self.is_valid(scene):
            return self._new(scene, name=name, status=status, room=room,
                        floor=floor, comment=comment)
        else:
            return False

    def remove(self, scene):
        """
        Delete a scene.
        """
        if self.is_valid(scene):
            self._store.remove(scene)
            return self._remove(scene)
        else:
            return False

    def add_device(self, scene, device, channel=-1, level=100,
                faderate=0, location=None):
        """
        Add a new device to scene.
        """
        if self.is_valid(scene) and device != None:
            if not device in self._scenes[scene]["devices"]:
                self._scenes[scene]["devices"][device] = {}
            self._scenes[scene]["devices"][device][channel] = {"level":level,
                                         "fade-rate":faderate}
            #print "channel=%s" % channel
            return True
        else:
            return False

    def del_device(self, scene, device, channel=-1):
        """
        Delete a device from a scene.
        """
        #print "device=%s" % device
        #print "channel=%s" % channel
        if self.is_valid(scene) and device in self._scenes[scene]["devices"]:
            if channel == "0":
                del (self._scenes[scene]["devices"][device])
            else :
                if channel in self._scenes[scene]["devices"][device] :
                    del (self._scenes[scene]["devices"][device][channel])
                if len(self._scenes[scene]["devices"][device]) == 0:
                    del (self._scenes[scene]["devices"][device])
            return True
        else:
            return False

    def is_valid(self, scene):
        """
        Return True if the scene is valid.
        """
        return scene != None and scene in self._scenes

    def count(self):
        """
        Return the number of scenes.
        """
        return len(self._scenes)

    def device_count(self, scene):
        """
        Return the number of devices in the scene.
        """
        count = 0
        for dev in self._scenes[scene]["devices"]:
            for ch in self._scenes[scene]["devices"][dev]:
                count = count+1
        return count

    def device_info(self, scene, device):
        """
        Return informations about a scene.
        """
        ret = list()
        for cha in self._scenes[scene]["devices"][device]:
            res = ""
            res = device + "," + str(cha)
            res = res + "," + str(self._scenes[scene]["devices"][device][cha]["level"])
            res = res+"," + str(self._scenes[scene]["devices"][device][cha]["fade-rate"])
            ret.append(res)
        return ret

    def device_scene_info(self, scene, device):
        """
        Return device configuration in a scene.
        """
        ret = list()
        for cha in self._scenes[scene]["devices"][device]:
            res = ""
            res = scene + "," + str(cha)
            res = res + "," + str(self._scenes[scene]["devices"][device][cha]["level"])
            res = res + "," + str(self._scenes[scene]["devices"][device][cha]["fade-rate"])
            ret.append(res)
        return ret

    def scene_device(self, device):
        """
        Return the list of scenes in which the device is.
        """
        liste = list()
        for scen in self._scenes:
            if device in self._scenes[scen]["devices"]:
                liste.extend(self.device_scene_info(scen, device))
        return liste

    def scenes(self):
        """
        Return the list of scenes.
        """
        res = ""
        for dev in self._scenes:
            if res == "":
                res = dev
            else:
                res = dev + "," + res
        return res

    def trig_scninfo(self, scene):
        """
        Trig an update on a scene
        """
        #print "scene info"
        mess = XplMessage()
        mess.set_type("xpl-trig")
        mess.set_schema("lighting.config")
        mess.add_data({"command" : "scninfo"})
        if not self.is_valid(scene):
            mess.add_data({"scene" : scene})
            mess.add_data({"status" : "not-found"})
        else:
            mess.add_data({"status" : self._scenes[scene]["status"]})
            mess.add_data({"scene" : scene})
            for field in self.fields:
                if field in self._scenes[scene] and \
                  self._scenes[scene][field] != None:
                    mess.add_data({field : self._scenes[scene][field]})
            mess.add_data({"device-count" :  self.device_count(scene)})
            for dev in self._scenes[scene]["devices"]:
                infs = self.device_info(scene, dev)
                for d in infs:
                    mess.add_data({"device" :  d})
        self._gateway.myxpl.send(mess)

    def cmnd_scninfo(self, myxpl, message):
        """
        @param myxpl : The XPL sender
        @param message : The XPL message

        lighting.request

        This allows a sender to learn about capabilities, networks, devices and scene that can be controlled and addressed

         request=[gateinfo|netlist|netinfo|devlist|devinfo|devstate|scnlist|scninfo]
         [network=ID]
         [[device=ID]|[scene=ID]][channel=#]

        lighting.devinfo

        Provides detailed information about a specific device

         network=ID
         device=ID
         status=[ok|not-found]
         name=[device name, if known]
         report-on-manual=[true|false]
         [room=room name]
         [floor=floor name]
         [comment=comments]
         [manufacturer=id,name]
         [product=id,name]
         [firmware-version=x.y]
         channel-count=#
         primary-channel=#
         channel=#,is-dimmable (true/false),default-fade-rate,level(0-100)
         scene-count=#
         scene=sceneID,channel,level,fade-rate
        """
        #print "scene info"
        mess = XplMessage()
        mess.set_type("xpl-stat")
        mess.set_schema("lighting.config")
        mess.add_data({"command" : "scninfo"})
        scene = None
        if 'scene' in message.data:
            scene = message.data['scene']
        if 'client' in message.data:
            mess.add_data({"client" : message.data['client']})
        if not self.is_valid(scene):
            mess.add_data({"scene" : scene})
            mess.add_data({"status" : "not-found"})
        else:
            mess.add_data({"status" : self._scenes[scene]["status"]})
            mess.add_data({"scene" : scene})
            for field in self.fields:
                if field in self._scenes[scene] and \
                  self._scenes[scene][field] != None:
                    mess.add_data({field : self._scenes[scene][field]})
            mess.add_data({"device-count" :  self.device_count(scene)})
            for dev in self._scenes[scene]["devices"]:
                infs = self.device_info(scene, dev)
                for d in infs:
                    mess.add_data({"device" :  d})
        myxpl.send(mess)

    def cmnd_scnlist(self, myxpl, message):
        """
        Return the list of scenes
        @param myxpl : The XPL sender
        @param message : The XPL message

        lighting.request

        This allows a sender to learn about capabilities, networks, scenes and scene that can be controlled and addressed

         request=[gateinfo|netlist|netinfo|devlist|devinfo|devstate|scnlist|scninfo]
         [network=ID]
         [[scene=ID]|[scene=ID]][channel=#]

        lighting.devlist

        Enumerates the valid scenes on a network

         network=ID
         status=[ok|not-found]
         scene-count=#
         scene=ID,ID,ID,ID...

        """
        #print "scene list"
        mess = XplMessage()
        mess.set_type("xpl-stat")
        mess.set_schema("lighting.config")
        if 'client' in message.data:
            mess.add_data({"client" : message.data['client']})
        mess.add_data({"command" : "scnlist"})
        mess.add_data({"status" : "ok"})
        mess.add_data({"scene-count" : self.count()})
        mess.add_data({"scenes" : self.scenes()})
        myxpl.send(mess)

    def cmnd_scnadd(self, myxpl, message):
        """
        Add a scene
        @param myxpl : The XPL sender
        @param message : The XPL message

        lighting.config

         scene=ID
         device=ID
         name=scene name
        """
        mess = XplMessage()
        mess.set_type("xpl-trig")
        mess.set_schema("lighting.config")
        mess.add_data({"command" : "scnadd"})
        scene = None
        if 'scene' in message.data:
            scene = message.data['scene']
        if self.is_valid(scene):
            mess.add_data({"scene" : scene})
            mess.add_data({"status" : "already-exist"})
        else:
            mess.add_data({"status" : "ok"})
            mess.add_data({"scene" : scene})
            name = None
            if 'name' in message.data:
                name = message.data['name']
            room = None
            if 'room' in message.data:
                room = message.data['room']
            floor = None
            if 'floor' in message.data:
                floor = message.data['floor']
            comment = None
            if 'comment' in message.data:
                comment = message.data['comment']
            self.new(scene, name=name, room=room, floor=floor, comment=comment)
        myxpl.send(mess)

    def cmnd_scndel(self, myxpl, message):
        """
        Delete a scene
        @param myxpl : The XPL sender
        @param message : The XPL message

        lighting.config

         scene=ID
         device=ID
         name=scene name
        """
        mess = XplMessage()
        mess.set_type("xpl-trig")
        mess.set_schema("lighting.config")
        mess.add_data({"command" : "scndel"})
        scene = None
        if 'scene' in message.data:
            scene = message.data['scene']
        if not self.is_valid(scene):
            mess.add_data({"scene" : scene})
            mess.add_data({"status" : "not-found"})
        else:
            mess.add_data({"status" : "ok"})
            mess.add_data({"scene" : scene})
            self._scenes[scene]["devices"] = {}
            self.trig_scninfo(scene)
            self.remove(scene)
        myxpl.send(mess)

    def cmnd_scnadddev(self, myxpl, message):
        """
        Add a device to a scene
        @param myxpl : The XPL sender
        @param message : The XPL message

        lighting.config

         scene=ID
         device=ID
         channel=#,level(0-100),fade-rate(0)
        """
        mess = XplMessage()
        mess.set_type("xpl-trig")
        mess.set_schema("lighting.config")
        mess.add_data({"command" : "scnadddev"})
        scene = None
        if 'scene' in message.data:
            scene = message.data['scene']
        if not self.is_valid(scene):
            mess.add_data({"scene" : scene})
            mess.add_data({"status" : "not-found"})
        else:
            mess.add_data({"scene" : scene})
            device = None
            if 'device' in message.data:
                device = message.data['device']
            if device == None:
                mess.add_data({"status" : "parameter-not-found"})
            elif device in self._scenes[scene]:
                mess.add_data({"device" : device})
                mess.add_data({"status" : "already-exist"})
            else:
                mess.add_data({"device" : device})
                if "channel" not in message.data:
                    mess.add_data({"status" : "parameter-not-found"})
                else :
                    #print "channel = %s" % message.data["channel"]
                    if type(message.data["channel"]) == type("") :
                        #print "channel=%s" % channel
                        start, separator, end = str(message.data["channel"]).partition(",")
                        dchannel = start
                        #print "dchannel=%s" % dchannel
                        start, separator, end = end.partition(",")
                        dlevel = start
                        #print "dlevel=%s" % dlevel
                        start, separator, end = end.partition(",")
                        dfaderate = start
                        #print "dfaderate=%s" % dfaderate
                        self.add_device(scene, device, channel=dchannel, \
                            level=dlevel, faderate=dfaderate)
                    else :
                        for channel in message.data["channel"]:
                            #print "channel=%s" % channel
                            start, separator, end = str(channel).partition(",")
                            dchannel = start
                            #print "dchannel=%s" % dchannel
                            start, separator, end = end.partition(",")
                            dlevel = start
                            #print "dlevel=%s" % dlevel
                            start, separator, end = end.partition(",")
                            dfaderate = start
                            #print "dfaderate=%s" % dfaderate
                            self.add_device(scene, device, channel=dchannel, \
                                level=dlevel, faderate=dfaderate)
                    mess.add_data({"status" : "ok"})
                    self.trig_scninfo(scene)
                    self._store.save(scene, self._scenes[scene])
        myxpl.send(mess)


    def cmnd_scndeldev(self, myxpl, message):
        """
        Add a device to a scene
        @param myxpl : The XPL sender
        @param message : The XPL message

        lighting.config

         scene=ID
         device=ID
         channel=#,level(0-100),fade-rate(0)
        """
        mess = XplMessage()
        mess.set_type("xpl-trig")
        mess.set_schema("lighting.config")
        mess.add_data({"command" : "scndeldev"})
        scene = None
        if 'scene' in message.data:
            scene = message.data['scene']
        if not self.is_valid(scene):
            mess.add_data({"scene" : scene})
            mess.add_data({"status" : "not-found"})
        else:
            mess.add_data({"scene" : scene})
            device = None
            if 'device' in message.data:
                device = message.data['device']
            if device == None:
                mess.add_data({"status" : "parameter-not-found"})
            elif device in self._scenes[scene]:
                mess.add_data({"device" : device})
                mess.add_data({"status" : "already-exist"})
            else:
                mess.add_data({"device" : device})
                if "channel" not in message.data:
                    mess.add_data({"status" : "parameter-not-found"})
                elif type(message.data["channel"]) == type(""):
                    self.del_device(scene, device, channel=message.data["channel"])
                    mess.add_data({"status" : "ok"})
                    self.trig_scninfo(scene)
                    self._store.save(scene, self._scenes[scene])
                else :
                    for channel in message.data["channel"]:
                        #print "channel=%s" % channel
                        self.del_device(scene, device, channel=channel)
                    mess.add_data({"status" : "ok"})
                    self.trig_scninfo(scene)
                    self._store.save(scene, self._scenes[scene])
        myxpl.send(mess)

class LightingSceneStore():
    """
    Store the scenes in the filesystem. We use a ConfigParser file per scene.
    In the section [Scene], we store inforations about the scene : name,
    location and devices. devices is a separated comma list of devices used
    in the scene (=D1,D2,...)
    The configuration of the device is store in section [D1] using the
    format
    CHANNEL=LEVEL,FADERATE
    Sections [Scene] [D1] [Dn]
    """
    def __init__(self, log, data_dir):
        """
        Initialise the store engine. Create the directory if necessary.
        """
        self._log = log
        self._data_files_dir = data_dir
        self._log.debug("__init__ : Use directory %s" % \
                self._data_files_dir)
        if not os.path.isdir(self._data_files_dir):
            os.mkdir(self._data_files_dir, 0770)

    def load_all(self, add_scn_cb, add_dev_cb):
        """
        Load all scenes from the filesystem. Parse all the *.scn files
        in directory and call the callback method to add it to the scenes.
        """
        for scnfile in glob.iglob(self._data_files_dir + "/*.scn") :
            try :
                config = ConfigParser.ConfigParser()
                config.read(scnfile)
                self._log.debug("load_all : Load job from %s" % \
                        scnfile)
                room = None
                if config.has_option("Scene", "room"):
                    room = config.get("Scene", "room")
                floor = None
                if config.has_option("Scene", "floor"):
                    floor = config.get("Scene", "floor")
                comment = None
                if config.has_option("Scene", "comment"):
                    comment = config.get("Scene", "comment")
                scene = None
                if config.has_option("Scene", "name"):
                    scene = config.get("Scene", "name")
                devices = None
                if config.has_option("Scene", "devices"):
                    devices = str(config.get("Scene", "devices"))
                if scene != None :
                    add_scn_cb(scene, name=scene, room=room, floor=floor, comment=comment)
                    for device in devices.split(","):
                        if config.has_section(device):
                            for channel in config.options(device):
                                level, separator, faderate = \
                                    str(config.get(device, channel)).partition(",")
                                add_dev_cb(scene, device, int(channel), int(level), int(faderate))
                        else :
                            self._log.warning("load_all : find a device %s in devices but no section [%s] for configuration" % \
                        scene, scene)
                else :
                    self._log.warning("load_all : can't find scene name in file %s" % \
                scnfile)
            except :
                self._log.warning("load_all : Error reading scene file %s" % scnfile)

    def save(self, scene, data):
        """
        Save a scene to disk
        """
        config = ConfigParser.ConfigParser()

        # When adding sections or items, add them in the reverse order of
        # how you want them to be displayed in the actual file.
        # In addition, please note that using RawConfigParser's and the raw
        # mode of ConfigParser's respective set functions, you can assign
        # non-string values to keys internally, but will receive an error
        # when attempting to write to a file or when you get it in non-raw
        # mode. SafeConfigParser does not allow such assignments to take place.
        config.add_section('Scene')
        config.set('Scene', 'name', scene)
        if "room" in data:
            config.set('Scene', 'room', data["room"])
        if "floor" in data:
            config.set('Scene', 'floor', data["floor"])
        if "comment" in data:
            config.set('Scene', 'comment', data["comment"])
        devlist = ""
        if "devices" in data:
            for device in data["devices"]:
                config.add_section(device)
                for channel in data["devices"][device]:
                    value = data["devices"][device][channel]["level"] + "," + data["devices"][device][channel]["fade-rate"]
                    config.set(device, channel, value)
                if devlist == "" :
                    devlist = device
                else :
                    devlist = devlist + "," + device
        config.set('Scene', 'devices', devlist)
        # Writing our configuration file
        with open(self._get_scnfile(scene), 'wb') as configfile:
            config.write(configfile)

    def remove(self, scene):
        """
        Remove a scene from disk
        """
        os.remove(self._get_scnfile(scene))

    def _get_scnfile(self, scn):
        """
        Return the filename associated to a scn.
        """
        return os.path.join(self._data_files_dir, scn + ".scn")
