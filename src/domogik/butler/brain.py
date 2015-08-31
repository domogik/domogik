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

Plugin purpose
==============

This plugin manages scenarii, it provides MQ interface

Implements
==========


@author: Fritz SMH <fritz.smh at gmail.com>
@copyright: (C) 2007-2015 Domogik project
@license: GPL(v3)
@organization: Domogik
"""


from domogik.common.plugin import PACKAGES_DIR
from domogik.common.configloader import Loader, CONFIG_FILE
from domogikmq.message import MQMessage
from domogikmq.reqrep.client import MQSyncReq
import zmq
import traceback
import json
import os

### Brain preferences
# This file is included in the package domogik-brain-datatype
# It is used to help the below functions to find which sensor to use when a device has several sensors of the same
# datatype.
# For example, the plugin weather has a lot of DT_Temp sensors, but when we request for the current temperature, we
# want to get the data from one sensor!
BRAIN_PREFERENCES = "brain_base/preferences.json"


def get_packages_directory():
    cfg = Loader('domogik')
    my_conf = cfg.load()
    #self._config_files = CONFIG_FILE
    config = dict(my_conf[1])
    return os.path.join(config['libraries_path'], PACKAGES_DIR)



LEARN_FILE = os.path.join(get_packages_directory(), "butler_learn.rive")
STAR_FILE = os.path.join(get_packages_directory(), "butler_unknown_queries.log")


def get_sensor_value(dt_type, device_name, sensor_reference = None):
    """ If sensor_reference = None
            Search for a sensor matching the dt_type and the device name
        Else
            Search for a dedicated sensor matching the device_name
        @param dt_type : a domogik datatype : DT_Temperature, DT_Humidity, ...
        @param device_name : the device name
        @param sensor_reference : the sensor name
    """
    if isinstance(device_name, list):
        device_name = ' '.join(device_name)
    #print("Device name = {0}".format(device_name))
    #print("Datatype = {0}".format(dt_type))

    ### search for all devices of the appropriate dt_type 
    if sensor_reference:
        check_preferences = False
    else:
        check_preferences = True
    candidates = get_sensors_for_datatype(dt_type, check_preferences)
    print("Candidates for the appropriate datatype : {0}".format(candidates))

    if sensor_reference:
        ### then search for the sensor with the appropriate reference
        the_sensor = filter_sensors_by_reference_and_device_name(candidates, sensor_reference, device_name)
    else:
        ### then, search for any device that matches the device name
        the_sensor = filter_sensors_by_device_name(candidates, device_name)

    print("The sensor is : {0}".format(the_sensor))

    ### no corresponding sensor :(
    if the_sensor == None:
        return None

    ### corresponding sensor!
    # let's get the sensor value

    the_value = the_sensor['last_value']

    return the_value
    



def get_sensors_for_datatype(dt_type, check_preferences = True):
    """ Find the matching devices and features
    """

    if check_preferences:
        # TODO : upgrade to load only once and then keep in memory
        preferences_file = os.path.join(get_packages_directory(), BRAIN_PREFERENCES)
        try:
            preferences_fp = open(preferences_file)
            preferences = json.load(preferences_fp)
        except:
            print("Error while loading preferences (maybe no preferences file ? {0} : {1}".format(preferences_file, traceback.format_exc()))
            pass
    else:
        preferences = {}

    candidates = []

    cli = MQSyncReq(zmq.Context())
    msg = MQMessage()

    # TODO : improve by calling only from time to time and keep in memory
    msg.set_action('device.get')

    try:
        str_devices = cli.request('dbmgr', msg.get(), timeout=10).get()[1]
        devices = json.loads(str_devices)['devices']
        for a_device in devices:
            #print a_device
            # search in all sensors
            candidates_for_this_device = {}
            for a_sensor in a_device["sensors"]:
                if a_device["sensors"][a_sensor]["data_type"] == dt_type:
                    #print(a_device["sensors"][a_sensor])
                    candidates_for_this_device[a_sensor] = {"device_name" : a_device["name"],
                                                            "device_id" : a_device["id"],
                                                            "last_value" : a_device["sensors"][a_sensor]["last_value"],
                                                            "sensor_name" : a_device["sensors"][a_sensor]["name"],
                                                            "sensor_reference" : a_device["sensors"][a_sensor]["reference"],
                                                            "sensor_id" : a_device["sensors"][a_sensor]["id"]}
            # if there are several candidates for a device, we check if there are some preferences defined
            # and if so, we use them
            if len(candidates_for_this_device) > 1:
                package = a_device["client_id"].split(".")[0]
                #print("Check for preferences for the package '{0}'....".format(package))
                if preferences.has_key(package): 
                    if preferences[package].has_key(dt_type):
                        print("Preferences found for datatype '{0}' : sensor '{1}'".format(dt_type, preferences[package][dt_type]))
                        candidates.append(candidates_for_this_device[preferences[package][dt_type]])
                else:
                    # yes we have only one entry, but we need to get the value related to the key...
                    # so we use a for to get the unique key here and so get only the value
                    for key in candidates_for_this_device:
                        candidates.append(candidates_for_this_device[key])
            else:
                if candidates_for_this_device != {}:
                    # yes we have only one entry, but we need to get the value related to the key...
                    # so we use a for to get the unique key here and so get only the value
                    for key in candidates_for_this_device:
                        candidates.append(candidates_for_this_device[key])

        return candidates                
    except:
        print("ERROR : {0}".format(traceback.format_exc()))
        pass




def filter_sensors_by_reference_and_device_name(candidates, reference, device_name):
    """ find in the sensors list, the good one
        IF the device_name == None, we assume there is only one corresponding device
    """
    reference = reference.lower()
    if device_name != None:
        device_name = device_name.lower()
    for a_sensor in candidates:
        try:
            if device_name == None and a_sensor["sensor_reference"].lower() == reference:
                return a_sensor
            #print(device_name)
            #print(a_sensor["device_name"])
            if device_name == a_sensor["device_name"].lower() and a_sensor["sensor_reference"].lower() == reference:
                return a_sensor
        except:
            print("ERROR : {0}".format(traceback.format_exc()))
            pass

    return None
    
def filter_sensors_by_device_name(candidates, device_name):
    """ for each given sensor, check the most appropriate choice depending on device_name
    """
    device_name = device_name.lower()

    # first, check if we got an exact match !
    for a_sensor in candidates:
        try:
            if a_sensor["device_name"].lower() == device_name:
                return a_sensor
        except:
            print("ERROR : {0}".format(traceback.format_exc()))
            pass


    # TODO : add other checks (with syntax correction)

    return None


def learn(rs_code):
    """ Add some rivescript code in a file
        and requets to reload the brain
        @param rs_code : some rs_code. Example : 
                  + ping
                  - pong
    """
    with open(LEARN_FILE, "a") as file:
        file.write(rs_code) 

def trigger_bool_command(dt_type, device, value):
    try:
        device_name = device.lower()
        cli = MQSyncReq(zmq.Context())
        msg = MQMessage()
        msg.set_action('device.get')
        str_devices = cli.request('dbmgr', msg.get(), timeout=10).get()[1]
        devices = json.loads(str_devices)['devices']
        found = None
        for a_device in devices:
            if a_device['name'].lower() == device_name:
                cid = 0
                for a_command in a_device['commands']:
                    pid = 0
                    for a_param in a_device['commands'][a_command]['parameters']:
                        if a_param['data_type'] == dt_type:
                            found = [a_device, a_command, pid]
                            break
                        pid = pid + 1
                    else:
                        continue
                        cid = cid + 1
                    break
        if found:
            dev = found[0]
            cid = found[1]
            pid = found[2]
            cli = MQSyncReq(zmq.Context())
            msg = MQMessage()
            msg.set_action('cmd.send')
            msg.add_data('cmdid', dev['commands'][cid]['id'])
            msg.add_data('cmdparams', {dev['commands'][cid]['parameters'][pid]['key'] : value})
            return cli.request('xplgw', msg.get(), timeout=10).get()
        else:
            return None
    except:
        print("ERROR : {0}".format(traceback.format_exc()))
        return None


def process_star(query):
    """ function to process the '*' pattern :
        - store input query in a dedicated log file
        - ...
    """
    with open(STAR_FILE, "a") as file:
        file.write(query) 
