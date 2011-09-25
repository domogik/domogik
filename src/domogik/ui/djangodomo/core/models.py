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
from django.conf import settings
from htmlentitydefs import name2codepoint
import re
import simplejson
import dmg_pipes as pipes

def unescape(s):
    "unescape HTML code refs; c.f. http://wiki.python.org/moin/EscapingHtml"
    return re.sub('&(%s);' % '|'.join(name2codepoint),
              lambda m: unichr(name2codepoint[m.group(1)]), s)

class Rest(pipes.DmgPipe):
    uri = settings.INTERNAL_REST_URL + "/"

    @staticmethod
    def get_info():
        resp = Rest.objects.get()
        if resp :
            return resp
        
class House(object):
    def __init__(self):
        self.config = UIConfigs.get_by_reference('house', '0')
        if self.config.has_key('name') :
            self.name = self.config['name']

class Areas(pipes.DmgPipe):
    uri = settings.INTERNAL_REST_URL + "/base/area"

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
            area.config = UIConfigs.get_by_reference('area', area.id)

            # If has rooms
            if hasattr(area, 'room') and (area.room):
                for room in area.room:
                    room.config = UIConfigs.get_by_reference('room', room.id)

class Rooms(pipes.DmgPipe):
    uri = settings.INTERNAL_REST_URL + "/base/room"

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
            room.config = UIConfigs.get_by_reference('room', room.id)

            # If is associated with area
            if hasattr(room, 'area') and (room.area) :
                room.area.config = UIConfigs.get_by_reference('area', room.area.id)

class Devices(pipes.DmgPipe):
    uri = settings.INTERNAL_REST_URL + "/base/device"

    @staticmethod
    def get_all():
        resp = Devices.objects.get({'parameters':"list"})
        if resp :
            return resp

    def merge_uiconfig(self):
        for device in self.device:
            # If is associated with room
            if hasattr(device, 'room') and (device.room) :
                device.room.config = UIConfigs.get_by_reference('room', device.room.id)

    def merge_features(self):
        for device in self.device:
            features = Features.get_by_device(device.id)
            device.features = features.feature
#            associations = FeatureAssociations.get_by_feature(feature.id)
#            for feature in device.feature:
#                for association in associations.feature_association:
#                    if (feature.id == association.device_feature_id):
#                        feature.association = association

class DeviceTechnologies(pipes.DmgPipe):
    uri = settings.INTERNAL_REST_URL + "/base/device_technology"

    @staticmethod
    def get_all():
        resp = DeviceTechnologies.objects.get({'parameters':"list"})
        if resp :
            return resp

class DeviceTypes(pipes.DmgPipe):
    uri = settings.INTERNAL_REST_URL + "/base/device_type"
    _dict = None
    
    @staticmethod
    def get_all():
        resp = DeviceTypes.objects.get({'parameters':"list"})
        if resp :
            return resp
        
    @staticmethod
    def get_dict():
        if DeviceTypes._dict is None:
            print "device types downloading"
            types = DeviceTypes.get_all()
            DeviceTypes._dict = {}
            for type in types.device_type:
                DeviceTypes._dict[type.id] = type
        else:
            print "device types already downloaded"
        return DeviceTypes._dict

    @staticmethod
    def get_dict_item(key):
        dict = DeviceTypes.get_dict()
        return dict[key]

class DeviceUsages(pipes.DmgPipe):
    uri = settings.INTERNAL_REST_URL + "/base/device_usage"
    _dict = None

    @staticmethod
    def get_all():
        resp = DeviceUsages.objects.get({'parameters':"list"})
        if resp :
            return resp
    
    @staticmethod
    def get_dict():
        if DeviceUsages._dict is None:
            print "device usages downloading"
            usages = DeviceUsages.get_all()
            DeviceUsages._dict = {}
            for usage in usages.device_usage:
                DeviceUsages._dict[usage.id] = usage
        else:
            print "device usages already downloaded"
        return DeviceUsages._dict

    @staticmethod
    def get_dict_item(key):
        dict = DeviceUsages.get_dict()
        return dict[key]

class Features(pipes.DmgPipe):
    uri = settings.INTERNAL_REST_URL + "/base/feature"

    @staticmethod
    def get_by_id(id):
        resp = Features.objects.get({'parameters':"list/by-id/" + str(id)})
        if resp :
            return resp

    @staticmethod
    def get_by_device(device_id):
        resp = Features.objects.get({'parameters':"list/by-device_id/" + str(device_id)})
        if resp :
            return resp

class FeatureAssociations(pipes.DmgPipe):
    uri = settings.INTERNAL_REST_URL + "/base/feature_association"

    @staticmethod
    def get_by_house():
        resp = FeatureAssociations.objects.get({'parameters':"list/by-house"})
        if resp :
            return resp

    @staticmethod
    def get_by_area(area_id):
        resp = FeatureAssociations.objects.get({'parameters':"list/by-area/" + str(area_id)})
        if resp :
            return resp

    @staticmethod
    def get_by_room(room_id):
        resp = FeatureAssociations.objects.get({'parameters':"list/by-room/" + str(room_id)})
        if resp :
            return resp
        
    @staticmethod
    def get_by_feature(feature_id):
        resp = FeatureAssociations.objects.get({'parameters':"list/by-feature/" + str(feature_id)})
        if resp :
            return resp
    
class UIConfigs(pipes.DmgPipe):
    uri = settings.INTERNAL_REST_URL + "/base/ui_config"

    @staticmethod
    def get_by_key(name, key):
        resp = {}
        uiconfigs = UIConfigs.objects.get({'parameters':"list/by-key/" + name + "/" + key})
        if uiconfigs :
            for uiconfig in uiconfigs.ui_config:
                if (uiconfig.value) :
                    if (uiconfig.value[0] == '{') : # json structure 
                        resp[uiconfig.key] = simplejson.loads(unescape(uiconfig.value))
                    else :
                        resp[uiconfig.key] = uiconfig.value
            return resp

    @staticmethod
    def get_by_reference(name, reference):
        resp = {}
        uiconfigs = UIConfigs.objects.get({'parameters':"list/by-reference/" + name + "/" + str(reference)})
        if uiconfigs :
            for uiconfig in uiconfigs.ui_config:
                if (uiconfig.value) :
                    if (uiconfig.value[0] == '{') : # json structure 
                        resp[uiconfig.key] = simplejson.loads(unescape(uiconfig.value))
                    else :
                        resp[uiconfig.key] = uiconfig.value
            return resp
    
class Plugins(pipes.DmgPipe):
    uri = settings.INTERNAL_REST_URL + "/plugin"

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
    def get_detail(host, name):
        resp = Plugins.objects.get({'parameters':"detail/" + host + "/" + name})
        if resp :
            return resp

    @staticmethod
    def enable(host, name, action):
        resp = Plugins.objects.get({'parameters':action + "/" + host + "/" + name})
        if resp :
            return resp

class Accounts(pipes.DmgPipe):
    uri = settings.INTERNAL_REST_URL + "/account"

    @staticmethod
    def auth(login, password):
        resp = Accounts.objects.get({'parameters':"auth/" + login + "/" + password})
        if resp :
            return resp

    @staticmethod
    def get_user(id):
        resp = Accounts.objects.get({'parameters':"user/list/by-id/" + id})
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

class Stats(pipes.DmgPipe):
    uri = settings.INTERNAL_REST_URL + "/stats"

    @staticmethod
    def get_latest(id, key):
        resp = Stats.objects.get({'parameters':str(id) + "/" + key + "/latest"})
        if resp :
            return resp

class Packages(pipes.DmgPipe):
    uri = settings.INTERNAL_REST_URL + "/package"

    @staticmethod
    def get_list_repo():
        resp = Packages.objects.get({'parameters':"list-repo"})
        if resp :
            return resp
    
    @staticmethod
    def get_list():
        resp = Packages.objects.get({'parameters':"list"})
        if resp :
            return resp
    
    @staticmethod
    def get_list_installed():
        resp = Packages.objects.get({'parameters':"list-installed"})
        if resp :
            return resp
        
    @staticmethod
    def install(host, name, release):
        resp = Packages.objects.get({'parameters':"install/" + host + "/" + name + "/" + release})
        if resp :
            return resp
    
    @staticmethod
    def get_mode():
        resp = Packages.objects.get({'parameters':"get-mode"})
        if resp :
            return resp 
