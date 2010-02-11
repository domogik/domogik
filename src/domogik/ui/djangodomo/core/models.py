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
    def getAll():
        resp = Areas.objects.get({'parameters':"list/"})
 #       icons = Areas.objects.get({'parameters':"ui_config/list/by-key/area/icon"})
        if resp :
            return resp

    @staticmethod
    def getById(id):
        resp = Areas.objects.get({'parameters':"list/by-id/"+id})
        if resp :
            return resp

    def merge_uiconfig(self):
        for area in self.area:
            uiconfigs = UIConfigs.getByReference('area', area.id)
            area.config = {}
            for uiconfig in uiconfigs.ui_config:
                area.config[uiconfig.key] = uiconfig.value

class Rooms(pipes.DmgPipe):
    uri = "http://127.0.0.1:8080/base/room"

    @staticmethod
    def getAll():
        resp = Rooms.objects.get({'parameters':"list/"})
        if resp :
            return resp

    @staticmethod
    def getByArea(id):
        resp = Rooms.objects.get({'parameters':"list/by-area/"+id})
        if resp :
            return resp
    
    @staticmethod
    def getWithoutArea():
        resp = Rooms.objects.get({'parameters':"list/by-area/null"})
        if resp :
            return resp

    def merge_uiconfig(self):
        for room in self.room:
            uiconfigs = UIConfigs.getByReference('room', room.id)
            room.config = {}
            for uiconfig in uiconfigs.ui_config:
                room.config[uiconfig.key] = uiconfig.value

class UIConfigs(pipes.DmgPipe):
    uri = "http://127.0.0.1:8080/base/ui_config"
    
    @staticmethod
    def getByKey(name, key):
        resp = UIConfigs.objects.get({'parameters':"list/by-key/" + name + "/" + key})
        if resp :
            return resp
    
    @staticmethod
    def getByReference(name, reference):
        resp = UIConfigs.objects.get({'parameters':"list/by-reference/" + name + "/" + str(reference)})
        if resp :
            return resp