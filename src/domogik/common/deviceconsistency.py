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

Implements
==========

DeviceConsistency
DeviceConsistencyException

@author: Maikel Punie <maikel.punie@gmail.com>
@copyright: (C) 2007-2015 Domogik project
@license: GPL(v3)
@organization: Domogik
"""
from domogik.common.packagejson import PackageJson
from domogik.common.database import DbHelper
import json


class DeviceConsistencyException(Exception):
    """
    Package exception
    """
    
    def __init__(self, value):
        Exception.__init__(self)
        self.value = value

    def __str__(self):
        return repr(self.value)


class DeviceConsistency():
    """ DeviceConsistency class
        A class that takes as input a deviceId, and a json
        It will then check that all consistency stuff is met in the db
    """
    def __init__(self, device_json, plugin_json):
        self.d_json = device_json
        self.p_json = plugin_json

        self._validate_identity()
        self._validate_device_type()
        self._validate_command()
        self._validate_sensor()

    def _validate_identity(self):
        # check its the correct file
        if self.d_json["client_id"].split(".")[0] != self.p_json['identity']['package_id']:
            raise DeviceConsistencyException("The device ({0}) does not belong to this plugin ({1})".format(self.d_json["client_id"].split(".")[0], self.p_json['identity']['package_id']))
        # check the versions
        if self.d_json["client_version"] > self.p_json['identity']['version']:
            raise DeviceConsistencyException("The device ({0}) has a newer client version then the plugin ({1})".format(self.d_json["client_version"], self.p_json['identity']['version']))
        #if self.d_json["client_version"] < self.p_json['identity']['version']:
        #    raise DeviceConsistencyException("The device ({0}) has an older client version then the plugin ({1})".format(self.d_json["client_version"], self.p_json['identity']['version']))

    def _validate_device_type(self):
        # check if the device_type exists
        if self.d_json['device_type_id'] not in self.p_json['device_types'].keys():
            raise DeviceConsistencyException("Device type {0} is not known by this plugin".format(self.d_json['device_type_id']))
        # TODO non-xpl params
        # TODO xpl params in every xpl_stat/xpl_command

    def _validate_command(self):
        # check that all commands for a device_type exists
        for cmd in self.p_json['device_types'][self.d_json['device_type_id']]["commands"]:
            if cmd not in self.d_json['commands'].keys():
                raise DeviceConsistencyException("Command ({0}) is in the plugin but not in the device".format(cmd))
            # check that all parameters for a command are present
            for param in self.p_json['commands'][cmd]['parameters']:
                found = False
                for cmdid, cmd in self.d_json['commands'].items():
                    for dparam in cmd['parameters']:
                        if param['key'] == dparam['key']:
                            if param['data_type'] != dparam['data_type']:
                                raise DeviceConsistencyException("Command parameter ({0}) datatype in the json ({1}) is not the same as in the db ({2})".format(param['key'], param['key'], dparam['key']))
                            found = True
                if not found:
                    raise DeviceConsistencyException("command parameter ({0}) found in the json but not in the db".format(param))
            # check that all xpl_commands exists + all params are there
            if cmd['xpl_command'] not in self.d_json['xpl_commands'].keys():
                raise DeviceConsistencyException("Xpl command ({0}) is in the plugin but not in the device".format(cmd['xpl_command']))
            self._validate_xpl_command(cmd['xpl_command'])

    def _validate_sensor(self):
        # check that all sensors exists
        for sen in self.p_json['device_types'][self.d_json['device_type_id']]["sensors"]:
            if sen not in self.d_json['sensors'].keys():
                raise DeviceConsistencyException("Sensor ({0}) is in the plugin but not in the device".format(sen))

    def _validate_xpl_command(self, cmd):
        print "TODO xpl command {0}".format(cmd)

    def _validate_xpl_stat(Self, stat):
        # check that all xpl_stats exist + all params are there
        print "TODO xpl stat {0}".format(stat)

if __name__ == "__main__":
    db = DbHelper()
    with db.session_scope():
        device_json = db.get_device(85)
    device_json = json.loads(json.dumps(device_json))
    plugin_json = PackageJson(name="velbus")
    DeviceConsistency(device_json, plugin_json.json)
