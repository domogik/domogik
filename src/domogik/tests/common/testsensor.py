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



from domogik.tests.common.helpers import get_rest_url
from domogik.common.utils import get_sanitized_hostname
import requests
import json
import sys


class TestSensor():
    """ Tool to handle sensors
    """

    def __init__(self, device_id, sensor_reference):
        """ Construtor
            @param rest_url : url of the rest server
            @param sensor_reference : sensor reference
        """
        # rest url
        self.rest_url = get_rest_url()

        # package informations
        self.device_id = device_id
        self.sensor_reference = sensor_reference
        try:
            self.sensor_id = self.get_sensor_id()
        except:
            self.sensor_id = None


    def get_sensor_id(self):
        """ Call GET /device/<id> to get the sensor id corresponding to the sensor name
        """
        print(u"Get the sensor id for device_id={0}, sensor_reference={1}".format(self.device_id, self.sensor_reference))
        response = requests.get("{0}/device/{1}".format(self.rest_url, self.device_id), \
                                 headers={'content-type':'application/x-www-form-urlencoded'})
        print(u"Response : [{0}]".format(response.status_code))
        #print(u"Response : [{0}] {1}".format(response.status_code, response.text))
        if response.status_code != 200:
            raise RuntimeError("Error when looking for the sensor id")

        # get the sensor id 
        device = json.loads(response.text)
        if not device['sensors'].has_key(self.sensor_reference):
            raise RuntimeError("There is no sensor named '{0}' for the device id {1}".format(self.sensor_reference, self.device_id))
        sensor_id = device['sensors'][self.sensor_reference]['id']

        # TODO  : nico's proposal that doesn't work :). To delete after checking with him what he wanted to do...
        #sensor_id = False
        #for sensor in device['sensors'] :
        #    if device['sensors'][sensor]['name'] == self.sensor_name:
        #        sensor_id = device['sensors'][sensor]['id']
        #        break
        #if not sensor_id:
        #     raise RuntimeError("There is no sensor named '{0}' for the device id {1}".format(self.sensor_name, self.device_id))
        print(u"The sensor id is '{0}'".format(sensor_id))
        return sensor_id


    def get_last_value(self):
        """ Call GET /sensor/<id> to get the last value of the sensor
            Returns a tuple : (timestamp, value)
        """
        print(u"Get the last value for sensor id={0} / name={1}".format(self.sensor_id, self.sensor_reference))
        response = requests.get("{0}/sensor/{1}".format(self.rest_url, self.sensor_id), \
                                 headers={'content-type':'application/x-www-form-urlencoded'})
        print(u"Response : [{0}]".format(response.status_code))
        #print(u"Response : [{0}] {1}".format(response.status_code, response.text))
        if response.status_code != 200:
            raise RuntimeError("Error when looking for the sensor")

        # get the value
        sensor = json.loads(response.text)
        value = sensor['last_value']
        timestamp = sensor['last_received']
        print(u"Last value : timestamp = {0} / value = {1}".format(timestamp, value))
        return (timestamp, value)


        


if __name__ == "__main__":

    ts = TestSensor(1, "get_percent_used")
    print ts.get_last_value()
 

