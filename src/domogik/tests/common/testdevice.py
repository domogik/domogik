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



from domogik.common.utils import get_rest_url, get_rest_ssl
from domogik.common.utils import get_sanitized_hostname
import zmq
from zmq.eventloop.ioloop import IOLoop
from domogikmq.reqrep.client import MQSyncReq
from domogikmq.message import MQMessage

from datetime import datetime
import json
import sys
import re


class TestDevice():
    """ Tool to create test devices
    """

    def __init__(self):
        """ Construtor
            @param rest_url : url of the rest server
        """
        # rest url
        self.rest_url = get_rest_url()
        self.rest_ssl = get_rest_ssl()

        # package informations
        self.client_id = None

        # device informations
        self.device_name = None
        self.device_type = None

    def get_params(self, client_id, device_type):
        """CALL GET /device/params/<device_Type>
        """
        print(u"{0} : Getting device_type params {1}".format(datetime.now(), device_type))
        cli = MQSyncReq(zmq.Context())
        msg = MQMessage()
        msg.set_action('device.params')
        msg.add_data('device_type', device_type)
        msg.add_data('client_id', client_id)
        response = cli.request('admin', msg.get(), timeout=15)
        if response is not None:
            response = response.get_data()
            if 'result' in response :
                print(u"{0} : The params are: {1}".format(datetime.now(), response['result']))
                return response['result']
            else :
                raise RuntimeError("Error when getting devices param for {0} : {1}".format(client_id, response))
        else :
            raise RuntimeError("Error when getting devices param for {0}".format(client_id))

    def create_device(self, params):
        """ Call POST /device/... to create the device
            @param params : The filled params
            @return : the device id for the device created
        """
        print(u"{0} : Create a test device <{1}> with {2} device type".format(datetime.now(), params['name'], params['device_type']))
        cli = MQSyncReq(zmq.Context())
        msg = MQMessage()
        msg.set_action('device.create')
        msg.set_data({'data': params})
        response = cli.request('admin', msg.get(), timeout=20)
        if response is not None:
            response = response.get_data()
            if 'result' in response :
                print(u"{0} : The new device is: {1}".format(datetime.now(), response['result']))
                return response['result']
            else :
                raise RuntimeError("Error when creating the device : {0} : {1}".format(params, response))
        else :
            raise RuntimeError("Error when creating the device : {0}".format(params))

    def del_device(self, id):
        """ Call DELETE /device/... to delete a device
            @param id : device id
        """
        print(u"{0} : Delete the device : id = {1}".format(datetime.now(), id))
        cli = MQSyncReq(zmq.Context())
        msg = MQMessage()
        msg.set_action('device.delete')
        msg.add_data('did', id)
        response = cli.request('admin', msg.get(), timeout=15)
        if response is not None:
            response = response.get_data()
            print(u"{0} : Delete response : {1}".format(datetime.now(), response))
        else :
            raise RuntimeError("Error when deleting the device")

    def del_devices_by_client(self, client_id):
        """ Call GET /device to get all devices
            Then, call del_device for each device of the given client_id
            @param client_id: the client id for which we want to delete all the devices
        """
        print(u"{0} : Delete all the devices for the client id '{1}'".format(datetime.now(), client_id))
        # first, retrieve all the devices
        clId = clId = re.split(r"[-.]+", client_id)
        cli = MQSyncReq(zmq.Context())
        msg = MQMessage()
        msg.set_action('device.get')
        msg.add_data('type', clId[0])
        msg.add_data('name', clId[1])
        msg.add_data('host', clId[2])
        response = cli.request('admin', msg.get(), timeout=15)
        if response is not None:
            response = response.get_data()
            print(u"{0} : Response : {1}".format(datetime.now(), response))
            if 'devices' in response:
                if response['devices'] == []:
                    print(u"{0} : There is no device to delete".format(datetime.now()))
                    return
                for device in response['devices']:
                    if device['client_id'] == client_id:
                        self.del_device(device['id'])
            else :
                raise RuntimeError("Error when getting devices list for {0} : {1}".format(client_id, response))
        else :
            raise RuntimeError("Error when getting devices list for {0}".format(client_id))


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

