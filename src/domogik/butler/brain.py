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

This library is part of the butler

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
import locale

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
    data = remove_accents(data)

    # remove duplicate spaces
    data = ' '.join(data.split())
    return data


#######################################################################
# public API

def get_sensor_value(log, devices, user_locale, dt_type, device_name, sensor_reference = None):
    value, _ = _get_sensor_data(log, devices, user_locale, dt_type, device_name, sensor_reference)
    return value

def get_sensor_value_and_date(log, devices, user_locale, dt_type, device_name, sensor_reference = None):
    value, date = _get_sensor_data(log, devices, user_locale, dt_type, device_name, sensor_reference)
    return value, date

def get_sensor_last_values_since(log, devices, user_locale, dt_type, device_name, sensor_reference = None, since = None):
    data, _ = _get_sensor_data(log, devices, user_locale, dt_type, device_name, sensor_reference, since)
    return data

# end of public API
#######################################################################

def _get_sensor_data(log, devices, user_locale, dt_type_list, device_name, sensor_reference = None, since = None):
    """ If sensor_reference = None
            Search for a sensor matching the dt_type and the device name
        Else
            Search for a dedicated sensor matching the device_name

        If since = None
            return <last value>, <last value date as timestamp>
        Else
            return <dict of last values>, None

        @param log : butler logger callback
        @param devices : butler devices in memory
        @param user_locale : the user locale
        @param dt_type_list : a list of domogik datatype : DT_Temperature, DT_Humidity, ...
        @param device_name : the device name
        @param sensor_reference : the sensor name
        @param since : if not None, get all values with last_received > since
                       else, get only the last value
    """
    # if several datatype have been provided
    dt_type_list = dt_type_list.split("|")
       
    if isinstance(device_name, list):
        device_name = ' '.join(device_name)
    log.info(u"Device name = {0}".format(device_name))
    log.info(u"Datatype(s) = {0}".format(dt_type_list))

    ### search for all devices of the appropriate dt_type 
    if sensor_reference:
        check_preferences = False
    else:
        check_preferences = True

    # get the devices
    # TODO : improve : refresh only when some devices are updated and get the last item from history instead
    #log.debug(u"Request the devices list over MQ...")
    #try:
    #    cli = MQSyncReq(zmq.Context())
    #    msg = MQMessage()
    #    msg.set_action('device.get')
    #    str_devices = cli.request('dbmgr', msg.get(), timeout=10).get()[1]
    #    devices = json.loads(str_devices)['devices']
    #except:
    #    log.error(u"Error while getting the devices list over MQ. Error is : ".format(traceback.format_exc()))
    #    return None, None

    # filter the candidates from all the devices
    candidates = get_sensors_for_datatype(devices, dt_type_list, check_preferences, log)
    log.info(u"Candidates for the appropriate datatype : {0}".format(candidates))

    if sensor_reference:
        ### then search for the sensor with the appropriate reference
        the_sensor = filter_sensors_by_reference_and_device_name(candidates, sensor_reference, device_name, log)
    else:
        ### then, search for any device that matches the device name
        the_sensor = filter_sensors_by_device_name(candidates, device_name, log)

    log.info(u"The sensor is : {0}".format(the_sensor))

    ### no corresponding sensor :(
    if the_sensor == None:
        return None, None

    ### corresponding sensor!
    # let's get the sensor value

    # get only the last value
    if since == None:
        #the_value = the_sensor['last_value']
        #last_received = the_sensor['last_received']

        # get the sensor last value over MQ
        cli = MQSyncReq(zmq.Context())
        msg = MQMessage()
        msg.set_action('sensor_history.get')
        msg.add_data('sensor_id', the_sensor['sensor_id'])
        msg.add_data('mode', 'last')
        res = cli.request('dbmgr', msg.get(), timeout=10).get()
        res = json.loads(res[1])
        the_value = res['values'][0]['value_str']
        last_received = res['values'][0]['timestamp']

        log.info(u"The value is : '{0}'".format(the_value))
    
        # do some checks to see if we should try to convert as a float or not
        do_convert = True
        if the_value != None and len(the_value) > 0:
            # if a value is a number but starts with a "0", it should be some special value which is not intented to
            # be converted
            if the_value[0] == "0":
                do_convert = False
    
        if do_convert:
            try:
                if len(user_locale.split(".")) > 1:     # fr_FR.UTF-8
                    the_locale = "{0}".format(user_locale)
                else:                                   # fr_FR
                    the_locale = "{0}.UTF-8".format(user_locale)
                #locale.setlocale(locale.LC_ALL, str("fr_FR.UTF-8"))
                locale.setlocale(locale.LC_ALL, the_locale)
                the_value = locale.format(u"%g", float(the_value))
            except:
                log.warning(u"Unable to format the value '{0}' as float/int with the locale '{1}'".format(the_value, the_locale))
        return the_value, last_received

    # get all the values since....
    else:
        try:
            # TODO : call a MQ message to get the values since the given parameter
            #        and then process
            log.info(u"Request sensor history over MQ for sensor_id={0} since {1}".format(the_sensor['sensor_id'], since))
            cli = MQSyncReq(zmq.Context())
            msg = MQMessage()
            msg.set_action('sensor_history.get')
            msg.add_data('sensor_id', the_sensor['sensor_id'])
            msg.add_data('mode', 'period')
            msg.add_data('from', since)
            res = cli.request('admin', msg.get(), timeout=10).get()
            if res == None:
                log.info(u"No history for this sensor since '{0}'".format(since))
                return None, None
            res = json.loads(res[1])
            if "values" in res:
                values = res['values']
            else:
                values = None
            log.info(u"The sensor history is : {0}".format(values))
            return values, None
        except:
            log.error(u"ERROR : {0}".format(traceback.format_exc()))
            return None, None
    

def is_float_and_not_int(x):
    try:
        a = float(x)
        b = int(x)
    except ValueError:
        return False
    else:
        return a == b


def get_sensors_for_datatype(devices, dt_type_list, check_preferences = True, log = None):
    """ Find the matching devices and features
    """

    if check_preferences:
        # TODO : upgrade to load only once and then keep in memory
        preferences_file = os.path.join(get_packages_directory(), BRAIN_PREFERENCES)
        try:
            preferences_fp = open(preferences_file)
            preferences = json.load(preferences_fp)
        except:
            log.error(u"Error while loading preferences (maybe no preferences file ? {0} : {1}".format(preferences_file, traceback.format_exc()))
            pass
        finally:
            preferences_fp.close()
    else:
        preferences = {}

    candidates = []

    # TODO DEL # cli = MQSyncReq(zmq.Context())
    # TODO DEL # msg = MQMessage()

    # TODO DEL # # TODO : improve by calling only from time to time and keep in memory
    # TODO DEL # msg.set_action('device.get')

    try:
        for a_device in devices:
            #print a_device
            # search in all sensors
            candidates_for_this_device = {}
            for a_sensor in a_device["sensors"]:
                if a_device["sensors"][a_sensor]["data_type"] in dt_type_list:
                    #print(a_device["sensors"][a_sensor])
                    candidates_for_this_device[a_sensor] = {"device_name" : a_device["name"],
                                                            "device_id" : a_device["id"],
                                                            "last_received" : a_device["sensors"][a_sensor]["last_received"],
                                                            "last_value" : a_device["sensors"][a_sensor]["last_value"],
                                                            "sensor_name" : a_device["sensors"][a_sensor]["name"],
                                                            "sensor_reference" : a_device["sensors"][a_sensor]["reference"],
                                                            "sensor_id" : a_device["sensors"][a_sensor]["id"]}
            # if there are several candidates for a device, we check if there are some preferences defined
            # and if so, we use them
            if len(candidates_for_this_device) > 1:
                package = a_device["client_id"].split(".")[0]
                #print(u"Check for preferences for the package '{0}'....".format(package))
                if preferences.has_key(package): 
                    for a_dt_type in dt_type_list:
                        if preferences[package].has_key(a_dt_type):
                            log.info(u"Preferences found for datatype '{0}' : sensor '{1}'".format(a_dt_type, preferences[package][a_dt_type]))
                            candidates.append(candidates_for_this_device[preferences[package][a_dt_type]])
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
        log.error(u"ERROR : {0}".format(traceback.format_exc()))
        pass




def filter_sensors_by_reference_and_device_name(candidates, reference, device_name, log):
    """ find in the sensors list, the good one
        IF the device_name == None, we assume there is only one corresponding device
    """
    log.info(u"Filter sensors by reference ({0}) and device name ({1})...".format(reference, device_name))
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
            log.error(u"ERROR : {0}".format(traceback.format_exc()))
            pass

    return None
    
def filter_sensors_by_device_name(candidates, device_name, log):
    """ for each given sensor, check the most appropriate choice depending on device_name
    """
    log.info(u"Filter sensors by device name ({0})...".format(device_name))
    device_name = clean_input(device_name)

    # first, check if we got an exact match !
    for a_sensor in candidates:
        try:
            if clean_input(a_sensor["device_name"]) == device_name:
                return a_sensor
        except:
            log.error(u"ERROR : {0}".format(traceback.format_exc()))
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

def do_command(log, devices, user_locale, dt_type_list, device, value, command_reference = None):
    """ Execute a command
        @log : logger object
        @user_locale : fr_FR, ...
        @dt_type_list : a datatype list
        @device : the device name on which we want to execute a command
        @value : the main value for the command

        # TODO : handle several values for complex commands

        @command_reference : if != None, a command reference
    """
    try:
        # if several datatype have been provided
        dt_type_list = dt_type_list.split("|")
       
        device_name = device.lower()
        log.debug(u"Command : search device. Device name = {0}".format(device_name))
        #cli = MQSyncReq(zmq.Context())
        #msg = MQMessage()
        #msg.set_action('device.get')
        #str_devices = cli.request('dbmgr', msg.get(), timeout=10).get()[1]
        #devices = json.loads(str_devices)['devices']
        found = None
        for a_device in devices:
            if clean_input(a_device['name']) == clean_input(device_name):
                for a_command in a_device['commands']:
                    pid = 0
                    for a_param in a_device['commands'][a_command]['parameters']:
                        if a_param['data_type'] in dt_type_list:
                            if command_reference == None:
                                found = [a_device, a_command, pid]
                                break
                            else:
                                if command_reference == a_command:
                                    found = [a_device, a_command, pid]
                                    break
                        pid += 1
                      
        #print("F={0}".format(found))
        if found:
            dev = found[0]
            cid = found[1]
            pid = found[2]
            log.debug(u"Command : device '{0}' found. id={1}, command id={2}, parameter id={3}".format(device_name, dev['id'], cid, pid))
            dt_type = dev['commands'][cid]['parameters'][pid]['data_type']
            cli = MQSyncReq(zmq.Context())
            msg = MQMessage()
            msg.set_action('cmd.send')
            msg.add_data('cmdid', dev['commands'][cid]['id'])
 
            # special case : for DT_Trigger, the value is always 1
            if dt_type == "DT_Trigger":
                msg.add_data('cmdparams', {dev['commands'][cid]['parameters'][pid]['key'] : 1})

            # special case : for DT_ColorRGBHexa, some values has to be translated
            # 1 = on => white = ffffff
            # 0 = off => black = 000000
            elif dt_type == "DT_ColorRGBHexa":
                if str(value) == "1":
                    value = "ffffff"
                elif str(value) == "0":
                    value = "000000"
                msg.add_data('cmdparams', {dev['commands'][cid]['parameters'][pid]['key'] : value})

            # classic case
            else:
                msg.add_data('cmdparams', {dev['commands'][cid]['parameters'][pid]['key'] : value})

            log.debug(u"Command : send command for device '{0}' : {1}".format(device_name, msg.get()))
            return cli.request('xplgw', msg.get(), timeout=10).get()
        else:
            return None
    except:
        log.error(u"ERROR : {0}".format(traceback.format_exc()))
        return None


def process_star(not_understood_responses, suggest_intro, rs):
    """ function to process the '*' pattern :
        - store input query in a dedicated log file
        - Try to see if we can suggest an alternate command to the user based on the suggestions list

        @param not_understood_responses : i18n responses for no matching suggestions
        @param suggest_intro : a start sentence (i18n) to suggest a match
        @param rs : rivescript brain
    """
    query = remove_accents(rs.query)
    suggests = rs.the_suggestions
    ### see if some suggestion matches
    found_suggest = False
    for a_suggest in suggests:
        for line in a_suggest.split('\n'):
            if len(line) > 0:
                if line[0] == "?":
                    regexp_raw = line[1:].strip()
                    regexp = remove_accents(regexp_raw)
                elif line[0] == "@":
                    shortcut = line
                    shortcut_sample = shortcut[1:].strip()
                else:
                    pass
        # strangely, on some installs, some regexp are not ok and raise a 'nothing to repeat' error
        # the below try.. except will catch them and avoid blocking the * feature
        try:
            m = re.match(regexp, query)
        except:
            rs.log.error(u"The following suggest is skipped due to an error. Suggest : '{0}'. Error : {1}".format(regexp, traceback.format_exc()))
            m = None

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
            file.write(query.encode('UTF-8')) 
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
    #print(u"{0}{1}".format(rs_comment, rs_code))
    learn(rs_code, comment = rs_comment)
    rs.reload_butler()


def remove_accents(input_str):
    """ Remove accents in utf-8 strings
    """
    nfkd_form = unicodedata.normalize('NFKD', input_str)
    return u"".join([c for c in nfkd_form if not unicodedata.combining(c)])
