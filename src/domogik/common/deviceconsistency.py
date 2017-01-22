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
import pprint

class DeviceConsistencyException(Exception):
    """
    Package exception
    """
    
    def __init__(self, code, value):
        Exception.__init__(self)
        self.value = value
        self.code = code

    def __str__(self):
        return repr(self.value)

class DeviceConsistency():
    """ DeviceConsistency class
        A class that takes as input a deviceId, and a json
        It will then check that all consistency stuff is met in the db
    """
    def __init__(self, check_type, device_json, plugin_json):
        """ __init__
        check_type = [raise|result]
        device_json = the current json of the device
        plugin_json = the current json for the plugin
        """
        self.d_json = device_json
        self.p_json = plugin_json
        self._type = check_type
        self._result = {}
        self._globaXplParams = []

    def check(self):
        self._validate_identity()
        self._validate_device_type()
        self._validate_command()
        self._validate_sensor()

    def get_result(self):
        if self._type == "raise":
            return None
        else:
            return self._result

    def _raise(self, code, data):
        """ Code
         0 DONE => nothing needs to be done, we raise anyway, data = string to raise
         1 DONE => sensor add
        -1 DONE => sensor remove
         2 DONE => command add
        -2 DONE => command remove
         3 DONE => command param add
        -3 DONE => command param remove
         4 DONE => xplcommand add
        -4 DONE => xplcommand remove
         5 => xplcommand_param add
        -5 => xplcommand_param remove
         6 DONE => xplstat add
        -6 => xplstat remove
         7 => xplstat_param add
        -7 => xplstat_param remove
         8 DONE => device_params add
        -8 DONE => device_params remove
        """
        if code == 0:
            raise DeviceConsistencyException(code, data)
        # SENSOR stuff
        elif code == 1:
            if self._type == "raise":
                raise DeviceConsistencyException(code, "Sensor ({0}) is in the plugin but not in the device".format(data))
            else:
                self._result['sensor_add'] = data
        elif code == -1:
            if self._type == "raise":
                raise DeviceConsistencyException(code, "Sensor ({0}) is in the device but not in the plugin".format(data))
            else:
                self._result['sensor_del'] = data
        # COMMAND stuff
        elif code == 2:
            if self._type == "raise":
                raise DeviceConsistencyException(code, "Command ({0}) is in the plugin but not in the device".format(data))
            else:
                self._result['command_add'] = data
        elif code == -2:
            if self._type == "raise":
                raise DeviceConsistencyException(code, "Command ({0}) is in the device but not in the plugin".format(data))
            else:
                self._result['command_del'] = data
        elif code == 3:
            if self._type == "raise":
                raise DeviceConsistencyException(code, "Command ({0}) parameter ({1}) found in the plugin but not in the db".format(data[0], data[1]))
            else:
                self._result['command_param_add'] = data
        elif code == -3:
            if self._type == "raise":
                raise DeviceConsistencyException(code, "Command ({0}) parameter ({1}) found in the db but not in the plugin".format(data[0], data[1]))
            else:
                self._result['command_param_del'] = data
        elif code == 4:
            if self._type == "raise":
                raise DeviceConsistencyException(code, "Xpl command ({0}) is in the plugin but not in the db".format(data))
            else:
                self._result['xplcommand_add'] = data
        elif code == -4:
            if self._type == "raise":
                raise DeviceConsistencyException(code, "Xpl command ({0}) is in db but not in the plugin".format(data))
            else:
                self._result['xplcommand_del'] = data
        elif code == 5:
            if self._type == "raise":
                raise DeviceConsistencyException(code, "Xpl command ({0}) parameter ({1}) found in the plugin but not in the db".format(data[0], data[1]))
            else:
                self._result['xplcommand_param_add'] = data
        elif code == -5:
            if self._type == "raise":
                raise DeviceConsistencyException(code, "Xpl command ({0}) parameter ({1}) found in the db but not in the plugin".format(data[0], data[1]))
            else:
                self._result['xplcommand_param_del'] = data
        elif code == 6:
            if self._type == "raise":
                raise DeviceConsistencyException(code, "Xpl stat ({0}) is in the plugin but not in the db".format(data))
            else:
                self._result['xplstat_add'] = data
        elif code == -6:
            if self._type == "raise":
                raise DeviceConsistencyException(code, "Xpl stat ({0}) is in db but not in the plugin".format(data))
            else:
                self._result['xplstat_del'] = data
        elif code == 7:
            if self._type == "raise":
                raise DeviceConsistencyException(code, "Xpl stat ({0}) parameter ({1}) found in the plugin but not in the db".format(data[0], data[1]))
            else:
                self._result['xplstat_param_add'] = data
        elif code == -7:
            if self._type == "raise":
                raise DeviceConsistencyException(code, "Xpl stat ({0}) parameter ({1}) found in the db but not in the plugin".format(data[0], data[1]))
            else:
                self._result['xplstat_param_del'] = data
        elif code == 8:
            if self._type == "raise":
                raise DeviceConsistencyException(code, "Device global param ({0}) is in the plugin but not in the device".format(data))
            else:
                self._result['device_param_add'] = data
        elif code == -8:
            if self._type == "raise":
                raise DeviceConsistencyException(code, "Device global param ({0}) is in the device but not in the plugin".format(data))
            else:
                self._result['device_param_del'] = data
        else:
            print "{0} = {1}".format(code, data)

    def _validate_identity(self):
        # check its the correct file
        if self.d_json["client_id"].split(".")[0] != self.p_json['identity']['package_id']:
            self._raise(0, "The device ({0}) does not belong to this plugin ({1})".format(self.d_json["client_id"].split(".")[0], self.p_json['identity']['package_id']))
        # check the versions
        if self.d_json["client_version"] > self.p_json['identity']['version']:
            self._raise(0, "The device ({0}) has a newer client version then the plugin ({1})".format(self.d_json["client_version"], self.p_json['identity']['version']))
        #if self.d_json["client_version"] == self.p_json['identity']['version']:
        #    self._raise(0, "The device ({0}) and the plugin ({1}) client version are the same".format(self.d_json["client_version"], self.p_json['identity']['version']))

    def _validate_device_type(self):
        # check if the device_type exists
        if self.d_json['device_type_id'] not in self.p_json['device_types'].keys():
            self._raise(0, "Device type {0} is not known by this plugin".format(self.d_json['device_type_id']))
        # global params (xpl and no-xpl)
        for param in self.p_json['device_types'][self.d_json['device_type_id']]['parameters']:
            if param['xpl']:
                # xpl params are chacked in the xpl procs, so cache them
                self._globaXplParams.append(param)
            elif param['key'] not in self.d_json['parameters'].keys():
                # a new param is added
                self._raise(8, param['key'])
        # removed params, in the db but not in the plugin
        for param in self.d_json['parameters'].keys():
            if not filter(lambda n: n['key'] == param, self.p_json['device_types'][self.d_json['device_type_id']]['parameters']):
                self._raise(-8, param)

    def _validate_command(self):
        # check that we need to remove commands
        for cmd in self.d_json['commands']:
            if cmd not in self.p_json['device_types'][self.d_json['device_type_id']]["commands"]:
                self._raise(-2, cmd)
        # check that all commands for a device_type exists
        for cmd in self.p_json['device_types'][self.d_json['device_type_id']]["commands"]:
            if cmd not in self.d_json['commands'].keys():
                self._raise(2, cmd)
            # check that all parameters for a command are present
            for param in self.p_json['commands'][cmd]['parameters']:
                found = False
                for cmdid, cmd in self.d_json['commands'].items():
                    for dparam in cmd['parameters']:
                        if param['key'] == dparam['key']:
                            if param['data_type'] != dparam['data_type']:
                                self._raise(0, "Command parameter ({0}) datatype in the json ({1}) is not the same as in the db ({2})".format(param['key'], param['key'], dparam['key']))
                            found = True
                if not found:
                    self._raise(3, (cmd, param))
            # check that all xpl_commands exists + all params are there
            if 'xpl_command' in cmd:
                if cmd['xpl_command'] not in self.d_json['xpl_commands'].keys():
                    self._raise(4, cmd['xpl_command'])
                self._validate_xpl_command(cmd['xpl_command'])
        # find old command params
        for cmdid, cmd in self.d_json['commands'].items():
            for param in cmd['parameters']:
                if not filter(lambda n: n['key'] == param['key'], self.p_json['commands'][cmdid]['parameters']):
                    self._raise(-3, (cmdid, param['key']) )
        # find old xplcommands
        for cmdid, cmd in self.d_json['xpl_commands'].items():
            found = False
            for pcmd in self.p_json['device_types'][self.d_json['device_type_id']]['commands']:
                if cmdid in self.p_json['xpl_commands']:
                    found = True
            if not found:
                self._raise(-4, cmdid )

    def _validate_sensor(self):
        # check that we need to remove sensors
        for sen in self.d_json['sensors']:
            if sen not in self.p_json['device_types'][self.d_json['device_type_id']]["sensors"]:
                self._raise(-1, sen)
        # check that all sensors exists
        for sen in self.p_json['device_types'][self.d_json['device_type_id']]["sensors"]:
            if sen not in self.d_json['sensors'].keys():
                self._raise(1, sen)
            # find an xplstat for this sensor (if there is one)
            for xplstat, stat in self.p_json['xpl_stats'].items():
                if filter(lambda n: n['sensor'] == sen, stat['parameters']['dynamic']):
                    if xplstat not in self.d_json['xpl_stats'].keys():
                        self._raise(6, xplstat)
                    self._validate_xpl_stat(xplstat)
        print "-6 TODO old linked xplstats for sensor"

    def _validate_xpl_command(self, cmd):
        print "TODO xpl command {0}".format(cmd)
        print "TODO xpl command params {0}".format(cmd)

    def _validate_xpl_stat(Self, stat):
        # check that all xpl_stats exist + all params are there
        print "TODO xpl stat {0}".format(stat)
        print "TODO xpl stat params {0}".format(stat)

if __name__ == "__main__":
    db = DbHelper()
    with db.session_scope():
        device_json = db.get_device(166)
        # 138
        # 100
    device_json = json.loads(json.dumps(device_json))
    plugin_json = PackageJson(name="test")
    # diskfree
    dc = DeviceConsistency("blah", device_json, plugin_json.json)
    dc.check()
    print dc.get_result()
