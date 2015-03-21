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
BRAIN_PREFERENCES = "brain_datatype/preferences.json"


# TODO : delete
#class DmgDevices:
#    """ This class is used to get informations about Domogik devices over the MQ
#    """
#
#    def __init__(self):
#        """ 
#        """ 
#        pass



def get_packages_directory():
    cfg = Loader('domogik')
    my_conf = cfg.load()
    #self._config_files = CONFIG_FILE
    config = dict(my_conf[1])
    return os.path.join(config['libraries_path'], PACKAGES_DIR)



def get_sensor_value(dt_type, device_name):
    """ Search for a sensor matching the dt_type and the device name
        @param dt_type : a domogik datatype : DT_Temperature, DT_Humidity, ...
        @param device_name : the device name
    """
    device_name = ' '.join(device_name)
    #print("Device name = {0}".format(device_name))
    #print("Datatype = {0}".format(dt_type))

    ### search for all devices of the appropriate dt_type 
    candidates = get_sensors_for_datatype(dt_type)
    #print("Candidates for the appropriate datatype : {0}".format(candidates))

    ### then, search for any device that matches the device name
    the_sensor = filter_sensors_by_device_name(candidates, device_name)

    ### no corresponding sensor :(
    if the_sensor == None:
        return None

    ### corresponding sensor!
    # let's get the sensor value

    the_value = get_sensor_last_value(the_sensor['sensor_id'])

    return the_value
    



def get_sensors_for_datatype(dt_type):
    """ Find the matching devices and features
    """

    # TODO : upgrade to load only once and then keep in memory
    preferences_file = os.path.join(get_packages_directory(), BRAIN_PREFERENCES)
    try:
        preferences_fp = open(preferences_file)
        preferences = json.load(preferences_fp)
    except:
        print("Error while loading preferences (maybe no preferences file ? {0} : {1}".format(preferences_file, traceback.format_exc()))
        pass

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
                    candidates_for_this_device[a_sensor] = {"device_name" : a_device["name"],
                                                            "device_id" : a_device["id"],
                                                            "sensor_name" : a_device["sensors"][a_sensor]["name"],
                                                            "sensor_id" : a_device["sensors"][a_sensor]["id"]}
            # if there are several candidates for a device, we check if there are some preferences defined
            # and if so, we use them
            if len(candidates_for_this_device) > 1:
                package = a_device["client_id"].split(".")[0]
                #print("Check for preferences for the package '{0}'....".format(package))
                if preferences.has_key(package): 
                    if preferences[package].has_key(dt_type):
                        #print("Preferences found for datatype '{0}' : sensor '{1}'".format(dt_type, preferences[package][dt_type]))
                        candidates.append(candidates_for_this_device[preferences[package][dt_type]])
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


def get_sensor_last_value(sensor_id):
    """ Get the last value of a sensor by its id
    """
    cli = MQSyncReq(zmq.Context())
    msg = MQMessage()
    msg.set_action('sensor_history.get')
    msg.add_data('sensor_id', sensor_id)
    try:
        value_str = cli.request('dbmgr', msg.get(), timeout=10).get()[1]
        value_json = json.loads(value_str)
        value = value_json['values'][0]
    except:
        print("ERROR : {0}".format(traceback.format_exc()))
        pass
    return value
