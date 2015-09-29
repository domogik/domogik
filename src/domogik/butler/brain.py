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


from domogik.common.plugin import PACKAGES_DIR, RESOURCES_DIR
from domogik.common.configloader import Loader, CONFIG_FILE
from domogikmq.message import MQMessage
from domogikmq.reqrep.client import MQSyncReq
import zmq
import traceback
import json
import os
import re
import unicodedata
from random import randint

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

def get_resources_directory():
    cfg = Loader('domogik')
    my_conf = cfg.load()
    #self._config_files = CONFIG_FILE
    config = dict(my_conf[1])
    return os.path.join(config['libraries_path'], RESOURCES_DIR)



LEARN_FILE = os.path.join(get_resources_directory(), "butler", "butler_learn.rive")
STAR_FILE = os.path.join(get_resources_directory(), "butler", "butler_not_understood_queries.log")


def clean_input(data):
    """ Remove some characters, accents, ...
    """
    if isinstance(data, str):
        data = unicode(data, 'utf-8')

    # put all in lower case
    data = data.lower()

    # remove blanks on startup and end
    data = data.strip()

    if len(data) == 0:
        return ""

    # remove last character if needed
    if data[-1] in ['.', '!', '?']:
        data = data[:-1]

    # remove non standard caracters
    data = data.replace(",", " ")
    data = data.replace("'", " ")
    data = data.replace("?", " ")
    data = data.replace("!", " ")

    # remove accents
    data = unicodedata.normalize('NFD', data).encode('ascii', 'ignore')

    # remove duplicate spaces
    data = ' '.join(data.split())
    return data


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
    print("Device name = {0}".format(device_name))
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
        device_name = clean_input(device_name)
    for a_sensor in candidates:
        try:
            if device_name == None and a_sensor["sensor_reference"].lower() == reference:
                return a_sensor
            if device_name == clean_input(a_sensor["device_name"]) and a_sensor["sensor_reference"].lower() == reference:
                return a_sensor
        except:
            print("ERROR : {0}".format(traceback.format_exc()))
            pass

    return None
    
def filter_sensors_by_device_name(candidates, device_name):
    """ for each given sensor, check the most appropriate choice depending on device_name
    """
    device_name = clean_input(device_name)

    # first, check if we got an exact match !
    for a_sensor in candidates:
        try:
            if clean_input(a_sensor["device_name"]) == device_name:
                return a_sensor
        except:
            print("ERROR : {0}".format(traceback.format_exc()))
            pass


    # TODO : add other checks (with syntax correction)

    return None


def learn(rs_code, comment = None):
    """ Add some rivescript code in a file
        and requets to reload the brain
        @param rs_code : some rs_code. Example : 
                  + ping
                  - pong
    """
    utf8_data = ""
    if comment != None:
        utf8_data += comment.encode('UTF-8')
    else:
        utf8_data += "// Added by the butler during a learning process\n"

    utf8_data += rs_code.encode('UTF-8')
    with open(LEARN_FILE, "a") as file:
        file.write(utf8_data + "\n\n") 

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


def process_star(not_understood_responses, suggest_intro, rs):
    """ function to process the '*' pattern :
        - store input query in a dedicated log file
        - Try to see if we can suggest an alternate command to the user based on the suggestions list

        @param not_understood_responses : i18n responses for no matching suggestions
        @param suggest_intro : a start sentence (i18n) to suggest a match
        @param rs : rivescript brain
    """
    query = rs.query
    suggests = rs.the_suggestions
    ### see if some suggestion matches
    found_suggest = False
    for a_suggest in suggests:
        for line in a_suggest.split('\n'):
            if len(line) > 0:
                if line[0] == "?":
                    regexp = line[1:].strip()
                elif line[0] == "@":
                    shortcut = line
                    shortcut_sample = shortcut[1:].strip()
                else:
                    pass
        m = re.match(regexp, query)
        if m != None:
            query_with_star = query
            #print(u"Suggest match for query : {0}".format(query))
            #print(u"Regexp : '{0}', found : {1}".format(regexp, m.groups()))
            for idx in range(0, len(m.groups())):
                #print(idx)
                #print(m.groups()[idx])
                pattern = u"<star{0}>".format(idx+1)
                #print(pattern)
                shortcut_sample = shortcut_sample.replace(pattern, m.groups()[idx])
                query_with_star = query_with_star.replace(m.groups()[idx], "*")
            found_suggest = True
            rs.last_suggestion_matched = {"regexp" : regexp,
                                          "query" : query,
                                          "query_with_star" : query_with_star,
                                          "shortcut" : shortcut,
                                          "shortcut_sample" : shortcut_sample}
            return u"{0} {1}".format(suggest_intro, shortcut_sample)

    ### log not understood queries
    if found_suggest == False:
        query = u"{0}\n".format(query)
        with open(STAR_FILE, "a") as file:
            file.write(query) 
        return not_understood_responses[randint(0, len(not_understood_responses)-1)]


def learn_from_suggestion(rs):
    """ function called by rivescript if 'process_star' found a matching suggest and the user accepts it
        @param rs : rivescript brain
    """
    #print(rs.last_suggestion_matched)
    ls = rs.last_suggestion_matched
    rs_comment = u""
    rs_comment += u"// learned from suggestions\n"
    rs_comment += u"// Query : {0}\n".format(ls['query'])
    rs_comment += u"// Regexp : {0}\n".format(ls['regexp'])
    rs_comment += u"// Shortcut : {0}\n".format(ls['shortcut'])
    rs_comment += u"// Shortcut sample: {0}\n".format(ls['shortcut_sample'])
    rs_code = u""
    rs_code += u"+ {0}\n".format(ls['query_with_star'])
    rs_code += u"{0}\n".format(ls['shortcut'])
    print(u"{0}{1}".format(rs_comment, rs_code))
    learn(rs_code, comment = rs_comment)
    rs.reload_butler()
