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
import dmg_pipes as pipes

class Areas(pipes.DmgPipe):
    uri = "http://127.0.0.1:8080/base/area"

    @staticmethod
    def get_all():
        resp = Areas.objects.get({'parameters':"list/"})
        if resp :
            return resp

    @staticmethod
    def get_all_with_rooms():
        resp = Areas.objects.get({'parameters':"list-with-rooms/"})
        if resp :
            return resp

    @staticmethod
    def get_by_id(id):
        resp = Areas.objects.get({'parameters':"list/by-id/"+id})
        if resp :
            return resp

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
    uri = "http://127.0.0.1:8080/base/room"

    @staticmethod
    def get_all():
        resp = Rooms.objects.get({'parameters':"list/"})
        if resp :
            return resp

    @staticmethod
    def get_by_id(id):
        resp = Rooms.objects.get({'parameters':"list/by-id/"+id})
        if resp :
            return resp

    @staticmethod
    def get_by_area(id):
        resp = Rooms.objects.get({'parameters':"list/by-area/"+id})
        if resp :
            return resp

    @staticmethod
    def get_without_area():
        resp = Rooms.objects.get({'parameters':"list/by-area//"})
        if resp :
            return resp

    @staticmethod
    def get_all_with_devices():
        resp = Rooms.objects.get({'parameters':"list-with-devices/"})
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

    def merge_actuators(self):
        for room in self.room:
            if hasattr(room, 'device') and (room.device != 'None') :
                for device in room.device:
                    actuators = DeviceActuators.get_by_type(device.type_id)
                    device.actuator = actuators.actuator_feature

class Devices(pipes.DmgPipe):
    uri = "http://127.0.0.1:8080/base/device"

    @staticmethod
    def get_all():
        resp = Devices.objects.get({'parameters':"list/"})
        if resp :
            return resp

    @staticmethod
    def get_without_room():
        resp = Devices.objects.get({'parameters':"list/by-room//"})
        if resp :
            return resp

    @staticmethod
    def get_by_room(id):
        resp = Devices.objects.get({'parameters':"list/by-room/"+id})
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

    def merge_actuators(self):
        for device in self.device:
            actuators = DeviceActuators.get_by_type(device.type_id)
            device.actuator = actuators.actuator_feature

class DeviceUsages(pipes.DmgPipe):
    uri = "http://127.0.0.1:8080/base/device_usage"

    @staticmethod
    def get_all():
        resp = DeviceUsages.objects.get({'parameters':"list/"})
        if resp :
            return resp

class DeviceTechnologies(pipes.DmgPipe):
    uri = "http://127.0.0.1:8080/base/device_technology"

    @staticmethod
    def get_all():
        resp = DeviceTechnologies.objects.get({'parameters':"list/"})
        if resp :
            return resp

class DeviceTypes(pipes.DmgPipe):
    uri = "http://127.0.0.1:8080/base/device_type"

    @staticmethod
    def get_all():
        resp = DeviceTypes.objects.get({'parameters':"list/"})
        if resp :
            return resp

class DeviceActuators(pipes.DmgPipe):
    uri = "http://127.0.0.1:8080/base/actuator_feature"

    @staticmethod
    def get_all():
        resp = DeviceActuators.objects.get({'parameters':"list/"})
        if resp :
            return resp

    @staticmethod
    def get_by_type(type_id):
        resp = DeviceActuators.objects.get({'parameters':"list/by-type_id/" + str(type_id)})
        if resp :
            return resp

class UIConfigs(pipes.DmgPipe):
    uri = "http://127.0.0.1:8080/base/ui_config"

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

class Modules(pipes.DmgPipe):
    uri = "http://127.0.0.1:8080/module"

    @staticmethod
    def get_all():
        resp = Modules.objects.get({'parameters':"list/"})
        if resp :
            return resp

    @staticmethod
    def get_by_name(name):
        resp = Modules.objects.get({'parameters':"list/by-name/" + name})
        if resp :
            return resp

class Accounts(pipes.DmgPipe):
    uri = "http://127.0.0.1:8080/account"

    @staticmethod
    def auth(login, password):
        resp = Accounts.objects.get({'parameters':"auth/" + login + "/" + password})
        if resp :
            return resp

    @staticmethod
    def get_all_users():
        resp = Accounts.objects.get({'parameters':"user/list/"})
        if resp :
            return resp

    @staticmethod
    def get_all_people():
        resp = Accounts.objects.get({'parameters':"person/list/"})
        if resp :
            return resp
