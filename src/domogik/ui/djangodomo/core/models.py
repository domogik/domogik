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

Module purpose
==============

Django models. It is not used, we have our own database model (see sql_schema.py)

Implements
==========


@author: Domogik project
@copyright: (C) 2007-2009 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

from django.db import models
from domogik.common.configloader import Loader

import dmg_pipes as pipes

# HTTP server ip and port
try:
    cfg_rest = Loader('rest')
    config_rest = cfg_rest.load()
    conf_rest = dict(config_rest[1])
    rest_ip = conf_rest['rest_server_ip']
    rest_port = conf_rest['rest_server_port']
    print "REST config found : (" + rest_ip + ":" + rest_port + ")"
except KeyError:
    # default parameters
    rest_ip = "127.0.0.1"
    rest_port = "8080"
    print "REST config not found : using default (127.0.0.1:8080)"

rest_url = "http://" + rest_ip + ":" + rest_port

class REST():
    
    @staticmethod
    def getIP():
        return rest_ip
    
    @staticmethod
    def getPort():
        return rest_port
    
class Areas(pipes.DmgPipe):
    uri = rest_url + "/base/area"

    @staticmethod
    def get_all():
        resp = Areas.objects.get({'parameters':"list"})
        if resp :
            return resp

    @staticmethod
    def get_by_id(id):
        resp = Areas.objects.get({'parameters':"list/by-id/" + str(id)})
        if resp :
            return resp

    def merge_rooms(self):
        for area in self.area:
            rooms = Rooms.get_by_area(area.id)
            area.room = rooms.room
            
    def merge_uiconfig(self):
        for area in self.area:
            uiconfigs = UIConfigs.get_by_reference('area', area.id)
            area.config = {}
            for uiconfig in uiconfigs.ui_config:
                area.config[uiconfig.key] = uiconfig.value

            # If has rooms
            if hasattr(area, 'room') and (area.room != 'None'):
                for room in area.room:
                    uiconfigs = UIConfigs.get_by_reference('room', room.id)
                    room.config = {}
                    for uiconfig in uiconfigs.ui_config:
                        room.config[uiconfig.key] = uiconfig.value

class Rooms(pipes.DmgPipe):
    uri = rest_url + "/base/room"

    @staticmethod
    def get_all():
        resp = Rooms.objects.get({'parameters':"list"})
        if resp :
            return resp

    @staticmethod
    def get_by_id(id):
        resp = Rooms.objects.get({'parameters':"list/by-id/" + str(id)})
        if resp :
            return resp

    @staticmethod
    def get_by_area(id):
        resp = Rooms.objects.get({'parameters':"list/by-area/" + str(id)})
        if resp :
            return resp

    @staticmethod
    def get_without_area():
        resp = Rooms.objects.get({'parameters':"list/by-area//"})
        if resp :
            return resp

    def merge_uiconfig(self):
        for room in self.room:
            uiconfigs = UIConfigs.get_by_reference('room', room.id)
            room.config = {}
            for uiconfig in uiconfigs.ui_config:
                room.config[uiconfig.key] = uiconfig.value

            # If is associated with area
            if hasattr(room, 'area') and (room.area != 'None') :
                uiconfigs = UIConfigs.get_by_reference('area', room.area.id)
                room.area.config = {}
                for uiconfig in uiconfigs.ui_config:
                    room.area.config[uiconfig.key] = uiconfig.value

class Devices(pipes.DmgPipe):
    uri = rest_url + "/base/device"

    @staticmethod
    def get_all():
        resp = Devices.objects.get({'parameters':"list"})
        if resp :
            return resp

    def merge_uiconfig(self):
        for device in self.device:
            # If is associated with room
            if hasattr(device, 'room') and (device.room != 'None') :
                uiconfigs = UIConfigs.get_by_reference('room', device.room.id)
                device.room.config = {}
                for uiconfig in uiconfigs.ui_config:
                    device.room.config[uiconfig.key] = uiconfig.value

    def merge_features(self):
        for device in self.device:
            features = DeviceFeatures.get_by_type(device.device_type_id)
            device.feature = features.device_type_feature

class DeviceUsages(pipes.DmgPipe):
    uri = rest_url + "/base/device_usage"

    @staticmethod
    def get_all():
        resp = DeviceUsages.objects.get({'parameters':"list"})
        if resp :
            return resp

class DeviceTechnologies(pipes.DmgPipe):
    uri = rest_url + "/base/device_technology"

    @staticmethod
    def get_all():
        resp = DeviceTechnologies.objects.get({'parameters':"list"})
        if resp :
            return resp

class DeviceTypes(pipes.DmgPipe):
    uri = rest_url + "/base/device_type"

    @staticmethod
    def get_all():
        resp = DeviceTypes.objects.get({'parameters':"list"})
        if resp :
            return resp

class DeviceFeatures(pipes.DmgPipe):
    uri = rest_url + "/base/device_type_feature"

    @staticmethod
    def get_by_type(type_id):
        resp = DeviceFeatures.objects.get({'parameters':"list/by-type_id/" + str(type_id)})
        if resp :
            return resp

class UIConfigs(pipes.DmgPipe):
    uri = rest_url + "/base/ui_config"

    @staticmethod
    def get_by_key(name, key):
        resp = UIConfigs.objects.get({'parameters':"list/by-key/" + name + "/" + key})
        if resp :
            return resp

    @staticmethod
    def get_by_reference(name, reference):
        resp = UIConfigs.objects.get({'parameters':"list/by-reference/" + name + "/" + str(reference)})
        if resp :
            return resp

    @staticmethod
    def get_general(reference):
        resp = {}
        uiconfigs = UIConfigs.objects.get({'parameters':"list/by-reference/general/" + str(reference)})
        if uiconfigs :
            for uiconfig in uiconfigs.ui_config:
                resp[uiconfig.key] = uiconfig.value
            return resp

class Plugins(pipes.DmgPipe):
    uri = rest_url + "/plugin"

    @staticmethod
    def get_all():
        resp = Plugins.objects.get({'parameters':"list"})
        if resp :
            return resp

    @staticmethod
    def get_by_name(name):
        resp = Plugins.objects.get({'parameters':"list/by-name/" + name})
        if resp :
            return resp

    @staticmethod
    def get_detail(name):
        resp = Plugins.objects.get({'parameters':"detail/" + name})
        if resp :
            return resp

class Accounts(pipes.DmgPipe):
    uri = rest_url + "/account"

    @staticmethod
    def auth(login, password):
        resp = Accounts.objects.get({'parameters':"auth/" + login + "/" + password})
        if resp :
            return resp

    @staticmethod
    def get_all_users():
        resp = Accounts.objects.get({'parameters':"user/list"})
        if resp :
            return resp

    @staticmethod
    def get_all_people():
        resp = Accounts.objects.get({'parameters':"person/list"})
        if resp :
            return resp
