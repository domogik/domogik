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


class TestDevice():
    """ Tool to create test devices
    """

    def __init__(self):
        """ Construtor
            @param rest_url : url of the rest server
        """
        # rest url        
        # Fix SSL exception for travis-ci TODO: Find why get_rest_url() concider use_ssl ?         
        self.rest_url = get_rest_url()
        #self.rest_url = get_rest_url().replace('https', 'http')
        
        # package informations
        self.client_id = None

        # device informations
        self.device_name = None
        self.device_type = None

    def get_params(self, client_id, device_type):
        """CALL GET /device/params/<device_Type>
        """
        url = "{0}/device/params/{1}/{2}".format(self.rest_url, client_id, device_type)
        print(u"Getting device_type params {0}".format(device_type))
        print(u"Url called is {0}".format(url))
        
        response = requests.get(url, verify=False)
        #print(u"Response : [{0}]".format(response.status_code))
        print(u"Response : [{0}] : {1}".format(response.status_code, response.text))
        if response.status_code != 200:
            raise RuntimeError("Can not get the device_type params : {0}".format(response.text))

        params = json.loads(response.text)
        print(u"The parasm are: {0}".format(params))
        return params

    def create_device(self, params):
        """ Call POST /device/... to create the device
            @param params : The filled params
            @return : the device id for the device created
        """
        url = "{0}/device/".format(self.rest_url)
        print(u"Create a test device with {0}".format(params))
        print(u"Url called is {0}".format(url))

        response = requests.post(url, \
            headers={'content-type':'application/x-www-form-urlencoded'}, \
            data="params={0}".format(json.dumps(params)))
        
        #print(u"Response : [{0}]".format(response.status_code))
        print(u"Response : [{0}] {1}".format(response.status_code, response.text))
        if response.status_code != 201:
            raise RuntimeError("Error when creating the device : {0}".format(response))
        else:
            dev = json.loads(response.text)
            print(u"The new device is: {0}".format(dev))
            return dev

    def del_device(self, id):
        """ Call DELETE /device/... to delete a device
            @param id : device id
        """
        url = "{0}/device/{1}".format(self.rest_url, id)
        print(u"Delete the device : id = {0}".format(id))
        print(u"Url called is {0}".format(url))
        response = requests.delete(url, \
                                 headers={'content-type':'application/x-www-form-urlencoded'})
        print(u"Response : [{0}]".format(response.status_code))
        if response.status_code != 201:
            raise RuntimeError("Error when deleting the device")

    def del_devices_by_client(self, client_id):
        """ Call GET /device to get all devices
            Then, call del_device for each device of the given client_id
            @param client_id: the client id for which we want to delete all the devices
        """
        url = "{0}/device/".format(self.rest_url)
        print(u"Delete all the devices for the client id '{0}'".format(client_id))
        print(u"Url called is {0}".format(url))
        # first, retrieve all the devices
        response = requests.get(url, \
                                 headers={'content-type':'application/x-www-form-urlencoded'})
        #print(u"Response : [{0}]".format(response.status_code))
        print(u"Response : [{0}] : {1}".format(response.status_code, response.text))
        if response.status_code != 200:
            raise RuntimeError("Error when configuring the device global parameters : {0}".format(response.text))
        if response.text == "":
            print(u"There is no device to delete")
            return
        devices = device = json.loads(response.text)
        for device in devices:
            #print(u"Id = {0} / Client_id = {1}".format(device['id'], device['client_id']))
            if device['client_id'] == client_id:
                self.del_device(device['id'])
        
        


if __name__ == "__main__":
    client_id = "plugin-diskfree.{0}".format(get_sanitized_hostname())
    td = TestDevice()
    params = td.get_params(client_id, "diskfree.disk_usage")

    # fill in the params
    params["device_type"] = "diskfree.disk_usage"
    params["name"] = "TestDevice"
    params["reference"] = "reference"
    params["description"] = "description"
    for idx, val in enumerate(params['global']):
        params['global'][idx]['value'] = 1
    for idx, val in enumerate(params['xpl']):
        params['xpl'][idx]['value'] = '/'

    # go and create
    td.create_device(params)

