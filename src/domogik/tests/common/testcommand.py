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

Purpose
=======

Tools for regression tests

Usage
=====

@author: Nico <nico84dev@gmail.com>
@copyright: (C) 2007-2013 Domogik project
@license: GPL(v3)
@organization: Domogik
"""


import zmq
from zmq.eventloop.ioloop import IOLoop
from domogik.mq.reqrep.client import MQSyncReq
from domogik.mq.message import MQMessage
from domogik.tests.common.helpers import get_rest_url
from domogik.common.utils import get_sanitized_hostname
from domogik.tests.common.testsensor import TestSensor
import requests
import json
import sys
import threading
import time


class TestCommand():
    """ Tool to handle commands
    """

    def __init__(self, managerTestCase, device_id, command_name):
        """ Construtor
            @param rest_url : url of the rest server
        """
        # rest url
        self.rest_url = get_rest_url()
        # package informations
        self.managerTestCase = managerTestCase
        self.device_id = device_id
        self.command_name = command_name
        try:
            self.command_id = self.get_command_id()
         #   self.sensor = TestSensor(device_id, "get_total_space")
        except:
            self.command_id = None
            self.sensor = None

    def set_command(self, command_name):
        """Set commande reference, for changing command to test"""
        if self.command_name != command_name :
            self.command_name = command_name
            try:
                self.command_id = self.get_command_id()
            except:
                self.command_id = None
            print (u"Command reference as changed to {0} , id {1}".format(self.command_name,  self.command_id))

    def get_command_id(self):
        """ Call GET /device/<id> to get the command id corresponding to the command name
        """
        print(u"Get the command id for device_id={0} and command_name={1}".format(self.device_id, self.command_name))
        response = requests.get("{0}/device/{1}".format(self.rest_url, self.device_id), \
                                 headers={'content-type':'application/x-www-form-urlencoded'})
        print(u"Response : [{0}]".format(response.status_code))
        if response.status_code != 200:
            raise RuntimeError("Error when looking for the command id")

        # get the command id 
        device = json.loads(response.text)
   #     print device
        if not device['commands'].has_key(self.command_name):
            print "There is no command named '{0}' for the device id {1}".format(self.command_name, self.device_id)
            raise RuntimeError("There is no command named '{0}' for the device id {1}".format(self.command_name, self.device_id))
        self._device = device
        command_id = device['commands'][self.command_name]['id']
        print(u"The command id is '{0}'".format(command_id))
        return command_id

    def get_return_confirmation(self):
        """Return True if cmd must have en ack msg
        """
        if self._device and self.command_name :
            return self._device['commands'][self.command_name]['return_confirmation'] 
        else : return False

    def get_XplStat_id(self):
        """Return  XplStat Json id corresponding to command id, return false if there is no return_confirmation.
        """
        if self._device and self.command_name :
            cmd = self._device['commands'][self.command_name]
            if cmd['return_confirmation'] :
                for xplAck in self._device['xpl_commands'] :
                    if xplAck == cmd['xpl_command'] :
                        xplstat = self._device['xpl_commands'][xplAck]['xpl_stat_ack']
                        if xplstat != "" : return xplstat
        return False

    def assert_Xpl_Stat_Ack_Wait(self, *xplMsg,  **kwargs) :
        """Assert a xpltrig for waiting ack form command result
        """
        print(u"Check that a message about xpl stat ack is sent. The message must be received once time.")
#        print xplMsg,  args
        schema,  data, statResult = xplMsg
        self.managerTestCase.assertTrue(self.managerTestCase.wait_for_xpl(xpltype = "xpl-trig",
                                  xplschema = schema,
                                  xplsource = "domogik-{0}.{1}".format(self.managerTestCase.name, get_sanitized_hostname()),
                                  data = data,
                                  timeout = 60))
        self.assert_get_last_command_in_db(statResult)

    def get_XplStat_fromAck(self, edata = None):
        """ Return XplStat ack  message data through a tuple (schema, data) corresponding to command id, if there is no return_confirmation return tuple (None, false).
        @params edata : key(s), value(s) who are expected with specific value
            type : dict 
        """
        xplstat = self.get_XplStat_id()
        if xplstat :
            schema = self._device['xpl_stats'][xplstat]['schema']
            data = {}
            statResult ={}
            for param in self._device['xpl_stats'][xplstat]['parameters']['static']:
                data[param['key']] = param['value']
            for param in self._device['xpl_stats'][xplstat]['parameters']['dynamic']:
                data[param['key']] = None
                statResult[param['key']] = None
            if edata :
                print "Xpl_Stat data required for ack : {0}".format(edata)
                for d in edata :
                    data[d] = edata[d]
                    statResult[d] = edata[d]
            return (schema,  data, statResult)
        else : return (None , False, None)
            
    def test_XplCmd(self, parameters = {}, statParams = None):
        """Send an Xpl cmd with statics parameters by request, if necessary start testcase listener for ack message and 
             check if insert in database is ok.
        """
        if self.get_return_confirmation() :
            schema,  data,  statResult = self.get_XplStat_fromAck(statParams)
            th = threading.Thread(None, self.assert_Xpl_Stat_Ack_Wait, "th_test_0110_xpl-ack_from_{0}".format(self.command_name), (schema,  data, statResult))
            th.start()
            time.sleep(1)
        else : 
            print (u"No ack required for {0}".format(self.command_name))
        if self._device and self.command_id :
            cli = MQSyncReq(zmq.Context())
            msg = MQMessage()
            msg.set_action('cmd.send')
            msg.add_data('cmdid', self.command_id)
            msg.add_data('cmdparams', parameters)
            print (u"Send xpl_cmnd {0}".format(self.command_name))
            cli.request('xplgw', msg.get(), timeout=10)
#            if self.get_return_confirmation() :
#                self.assert_get_last_command_in_db(statResult)
#            else : 
#                print (u"No ack required for {0}".format(self.command_name))
            return True
        else : return False

    def _get_sensors_ref(self, statResult):
        """Return the sensor_ref stucture of an xpl_stat_ack of the command.
            return dict :
                sensor : TestSensor object
                name : sensor_reference
                param : a dict with key and value to check
        """
        sensorsRef =[]
        xplStat = self.get_XplStat_id()
        if xplStat :
   #         print "dynamic params : {0}".format(self._device['xpl_stats'][xplStat]['parameters']['dynamic'])
            for aparam in self._device['xpl_stats'][xplStat]['parameters']['dynamic'] :
                # Check if sensor exist
                for sensorId in self._device['sensors']:
                    if aparam['sensor_name'] == sensorId:
                        dynParam = {}
                        for k in statResult:
                            if aparam['key'] == k: 
                                dynParam[k] = statResult[k]
                                break
                        sensor = TestSensor(self.device_id, sensorId)
                        sensorsRef.append({'sensor': sensor, 'name' : aparam['sensor_name'],  'param' : dynParam})
        return sensorsRef
        
    def assert_get_last_command_in_db(self, statResult):
        """ Call GET /sensor/<id> to get the last value of the command
            Returns a tuple : (timestamp, value)
        """
        print(u"Check that value(s) of the xPL message has been inserted in database")
        sensors = self._get_sensors_ref(statResult)
        for sensor in sensors:
            print(u"Check if value '{0}' inserted in database is : {1}".format(sensor['name'], sensor['param']))
            value = str(sensor['param'].values()[0])
            val = sensor['sensor'].get_last_value()
            if val[0] and val[1]:
                self.managerTestCase.assertTrue(val[1] == value)
            else : print(u"No value in database, can't compare to {0}".format(value))


if __name__ == "__main__":

    ts = Testcommand(1, "set_on-off")
    print ts.get_last_command()
 

