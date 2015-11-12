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

@author: Fritz SMH <fritz.smh@gmail.com>
@copyright: (C) 2007-2012 Domogik project
@license: GPL(v3)
@organization: Domogik
"""



from domogik.common.utils import get_rest_url
from domogik.common.utils import get_sanitized_hostname
import requests
import json
import sys
import time
from threading import Thread


class TestCommand():
    """ Tool to handle commands
    """

    def __init__(self, device_id, command_reference):
        """ Construtor
            @param rest_url : url of the rest server
            @param command_reference : command reference
        """
        # rest url
        self.rest_url = get_rest_url()

        # package informations
        self.device_id = device_id
        self.command_reference = command_reference
        try:
            self.command_id, self.command_keys = self.get_command_id()
        except:
            self.command_id = None
            self.command_keys = None


    def get_command_id(self):
        """ Call GET /device/<id> to get the command id corresponding to the command name
        """
        print(u"Get the command id for device_id={0}, command_reference={1}".format(self.device_id, self.command_reference))
        response = requests.get("{0}/device/{1}".format(self.rest_url, self.device_id), \
                                 headers={'content-type':'application/x-www-form-urlencoded'})
        print(u"Response : [{0}]".format(response.status_code))
        print(u"Response : [{0}] {1}".format(response.status_code, response.text))
        if response.status_code != 200:
            raise RuntimeError("Error when looking for the command id")

        # get the command id 
        device = json.loads(response.text)
        if not device['commands'].has_key(self.command_reference):
            raise RuntimeError("There is no command named '{0}' for the device id {1}".format(self.command_reference, self.device_id))
        command_id = device['commands'][self.command_reference]['id']
        command_keys = []
        for cmd_key in device['commands'][self.command_reference]['parameters']:
            command_keys.append(cmd_key["key"])

        print(u"The command id is '{0}'".format(command_id))
        print(u"The command keys are '{0}'".format(command_keys))
        return command_id, command_keys

    def send_command(self, value):
        thr_send_command = Thread(None,
                                  self._send_command_thr,
                                  "send_command",
                                  (value,),
                                  {})
        thr_send_command.start()


    def _send_command_thr(self, value):
        """ Send a command over REST url with value = value
            @param value : value
        """
        # check if value is a single value or a dict
        # if this is a single value, there is only one command parameter
        # else, there are several command parameters
        if isinstance(value, dict):
            url = "{0}/cmd/id/{1}?".format(self.rest_url, self.command_id)
            for param in self.command_keys:
                try:
                    url = "{0}{1}={2}&".format(url, param, value[param])
                except KeyError:
                    print("ERROR : there is no key '{0}' for this command!".format(param))
        else:
            url = "{0}/cmd/id/{1}?{2}={3}".format(self.rest_url, self.command_id, self.command_keys[0], value)

        print(u"Wait 2 seconds before calling a command...")
        time.sleep(2)
        print(u"Call the command id={0} / name={1}".format(self.command_id, self.command_reference))
        print(u"Url = {0}".format(url))
        response = requests.get(url, 
                                headers={'content-type':'application/x-www-form-urlencoded'})
        print(u"Response : [{0}]".format(response.status_code))
        #print(u"Response : [{0}] {1}".format(response.status_code, response.text))
        if response.status_code != 204:
            raise RuntimeError("Error when sending the command")




if __name__ == "__main__":

    tc = TestCommand(53, "switch_lighting2")
    tc.send_command(0)
    time.sleep(1)
    tc.send_command(1)
 

