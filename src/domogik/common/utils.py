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

Module purpose
==============

Miscellaneous utility functions

Implements
==========


@author: Marc SCHNEIDER <marc@mirelsol.org>
@copyright: (C) 2007-2012 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

from subprocess import Popen, PIPE
import os
import sys
import re
from netifaces import interfaces, ifaddresses, AF_INET, AF_INET6
from domogik.common.configloader import Loader, CONFIG_FILE
import datetime
import time
import unicodedata
from domogikmq.reqrep.client import MQSyncReq
from domogikmq.message import MQMessage

# used by is_already_launched
STARTED_BY_MANAGER = "NOTICE=THIS_PLUGIN_IS_STARTED_BY_THE_MANAGER"

REGEXP_PS_SEPARATOR = re.compile('[\s]+')

# to optimize get_sanitized_hostname()
HOSTNAME= os.uname()[1].lower().split('.')[0].replace('-','')[0:16]


def get_interfaces():
    return interfaces()

def get_ip_for_interfaces(interface_list=[], ip_type=AF_INET, log = None):
    """ Returns all ips that are available for the interfaces in the list
    @param interface_list: a list of interfaces to ge the ips for,
        if the list is empty it will retrun all ips for this system
    @param ip_type: what ip type to get, can be
        AF_INET: for ipv4
        AF_INET6: for ipv6
    @return: a list of ips
    """
    all = False
    if type(interface_list) is not list:
        assert "The interface_list should be a list"
    if len(interface_list) == 0 or interface_list == ['*']:
        all = True
        interface_list = interfaces()
    ips = []
    for intf in interface_list:
        intf = intf.strip()
        if intf in interfaces():
            try:
                for addr in ifaddresses(intf)[ip_type]:
                    ips.append(addr['addr'])
            except:
                if not all:
                    msg = "There is no such working network interface: {0}".format(intf)
                    if log != None:
                        log.error(msg)
                    else:
                        print("ERROR : {0}".format(msg))
                else:
                    msg = "The network interface '{0}' is not available".format(intf)
                    if log != None:
                        log.debug(msg)
                    else:
                        print("{0}".format(msg))
        else:
            assert "Interface {0} does not exist".format(intf)
            if log != None:
                log.error("Interface {0} does not exist".format(intf))
    return ips

def interface_has_ip(interface):
    if len(get_ip_for_interfaces([interface])) == 0:
        return False
    else:
        return True

def get_sanitized_hostname():
    """ Get the sanitized hostname of the host
    This will lower it and keep only the part before the first dot
    """
    #print(">>>>>> get_sanitized_hostname()")
    #return os.uname()[1].lower().split('.')[0].replace('-','')[0:16]
    return HOSTNAME

def ucode(my_string):
    """Convert a string into unicode or return None if None value is passed

    @param my_string : string value to convert
    @return a str string

    """
    return ucode2(my_string)


    #if my_string is not None:
    #    #print("ucode : {0}".format(type(my_string)))
    #    if type(my_string) == unicode:
    #        try:
    #            # the following line is here to test if an Unicode error would occur...
    #            foo = "bar{0}".format(my_string)
    #            return my_string
    #        except UnicodeEncodeError:
    #            return my_string.encode('utf8')
    #    elif not type(my_string) == str:
    #        return str(my_string).decode("utf-8")
    #    else:
    #        return my_string.decode("utf-8")
    #else:
    #    return None

def ucode2(my_string):
    """Convert a string into unicode or return None if None value is passed

    @param my_string : string value to convert
    @return a unicode string

    """
    # special case : data is None
    if my_string is None:
        return None
    # already in unicode, return unicode
    elif isinstance(my_string, unicode):
        return my_string

    # str
    elif isinstance(my_string, str):
        return unicode(my_string, "utf-8")

    # other type (int, float, boolean, ...)
    else:
        return unicode(str(my_string), "utf-8")



def call_package_conversion(log, plugin, method, value):
    """Load the correct module, and encode the value

    @param log: an instalce of a Logger
    @param plugin: the plugin (package) name
    @param method: what methode to load from the conversion class
    @param value: the value to convert
    @return the converted value or None on error

    """
    modulename = 'packages.plugin_{0}.conversions.{0}'.format(plugin)
    classname = '{0}Conversions'.format(plugin)
    try:
        module = __import__(modulename, fromlist=[classname])
    except ImportError as err:
        log.critical("Can not import module {0}: {1}".format(modulename, err))
        return value
    try:
        staticclass = getattr(module, classname)
        staticmethode = getattr(staticclass, method)
    except AttributeError as err:
        log.critical("Can not load class ({0}) or methode ({1}): {2}".format(classname, method, err))
        return value
    log.debug("calling {0}.{1}".format(staticclass, staticmethode))
    return staticmethode(value)

def is_already_launched(log, type, id, manager=True):
    """ Check if there are already some process for the component launched
        @param log : logger
        @param type : client type to check with pgrep
        @param id : client id to check with pgrep
        @param manager : do we need to find the STARTED_BY_MANAGER String?
        @return : is_launched : True/False
                  pid_list : list of the already launched processes pid
    """
    my_pid = os.getpid()

    # the manager add the STARTED_BY_MANAGER useless command to allow the client to ignore this command line when it checks if it is already laucnehd or not
    # the final 'grep -v sudo' is here to exclude the lines launched by sudo from the search : using sudo make 2 results be in the grep result : one with sudo and the other one with the command (but this second one is filtered thanks to its pid)
    # the grep -v mprof is there to allow run of memory profiler
    if manager:
        #cmd = "pgrep -lf {0} | grep -v {1} | grep python | grep -v ps | grep -v {2} | grep -v sudo | grep -v su | grep -v testrunner".format(id, STARTED_BY_MANAGER, my_pid)
        cmd = "ps aux | grep {0} | grep -v {1} | grep python | grep -v ps | grep -v {2} | grep -v sudo | grep -v su | grep -v testrunner | grep -v mprof | grep -v update | grep -v sysadmin".format(id, STARTED_BY_MANAGER, my_pid)
    else:
        cmd = "ps aux | grep {0} | grep python | grep -v ps | grep -v sudo | grep -v su | grep -v sysadmin".format(id)
    # the grep python is needed to avoid a client to not start because someone is editing the client with vi :)

    if log:
        log.info("Looking for launched instances of '{0}'".format(id))
    is_launched = False
    subp = Popen(cmd, shell=True, stdout=PIPE)
    pid_list = []
    # example of return :
    # fritz     7419  0.0  0.3 108604 13168 ?        S    15:17   0:00 /usr/bin/python /var/lib/domogik//domogik_packages/plugin_diskfree/bin/diskfree.py
    # fritz     7420  0.4  0.3 617068 15012 ?        Sl   15:17   0:01 /usr/bin/python /var/lib/domogik//domogik_packages/plugin_diskfree/bin/diskfree.py

    for line in subp.stdout:
        is_launched = True
        if log:
            log.info("Process found : {0}".format(line.rstrip("\n")))
        the_pid = REGEXP_PS_SEPARATOR.split(line)[1]
        pid_list.append(the_pid)
        #pid_list.append(line.rstrip("\n").split(" ")[0])
    subp.wait()
    if is_launched:
        if log:
            log.info("There are already existing processes.")
    else:
        if log:
            log.info("No existing process.")
    return is_launched, pid_list


def get_rest_url(noRest=False):
    """ Build and return the rest url
    """
    cfg = Loader('admin')
    config = cfg.load()
    conf = dict(config[1])
    ### get REST ip and port
    port = conf['port']
    interfaces = conf['interfaces']
    intf = interfaces.split(',')
    # get the first ip of the first interface declared
    ip = get_ip_for_interfaces(intf)[0]
    protocol = "http" if conf['use_ssl'] else "http"
    if noRest:
        return "{0}://{1}:{2}".format(protocol, ip, port)
    else:
        return "{0}://{1}:{2}/rest".format(protocol, ip, port)

def get_rest_ssl():
    """Return false if no ssl option.
       Or dict {key_file : <ssl_key from admin config>, cert_file : <ssl_certificate from admin config>"""
    cfg = Loader('admin')
    config = cfg.load()
    conf = dict(config[1])
    ### get SSL option
    if conf['use_ssl'] :
        return {'cert_file': conf['ssl_certificate'], 'key_file': conf['ssl_key']}
    else :
        return False

def get_rest_doc_path():
    """ return the REST API generated doc path
    """
    cfg = Loader('domogik')
    config = cfg.load()
    conf = dict(config[1])
    ### get libraries path
    path = conf['libraries_path']

    return "{0}/rest_doc_generated_during_install/".format(path)



def get_packages_directory():
    """ This function is already defined in the Plugin class, but this one is used by the admin in application.py
        TODO : see if there is a cleaner way to do this!
    """
    # global config
    cfg_global = Loader('domogik')
    config_global = cfg_global.load()
    conf_global = dict(config_global[1])
    return "{0}/{1}".format(conf_global['libraries_path'], "domogik_packages")

def get_libraries_directory():
    """ This function is already defined in the Plugin class, but this one is used by the admin in application.py
        TODO : see if there is a cleaner way to do this!
    """
    # global config
    cfg_global = Loader('domogik')
    config_global = cfg_global.load()
    conf_global = dict(config_global[1])
    return conf_global['libraries_path']

def get_data_files_directory_for_plugin(plugin_name):
    """ This function is already defined in the Plugin class, but this one is used by the admin in application.py
        In fact, this is not really the same function as this one takes one parameter
    """
    # global config
    cfg_global = Loader('domogik')
    config_global = cfg_global.load()
    conf_global = dict(config_global[1])
    return "{0}/{1}/plugin_{2}/data".format(conf_global['libraries_path'], "domogik_packages", plugin_name)


def get_seconds_since_midnight():
    now = datetime.datetime.now()
    return (now - now.replace(hour=0, minute=0, second=0, microsecond=0)).total_seconds()


def get_midnight_timestamp():
    ts = time.time()
    return int(ts - get_seconds_since_midnight())

def remove_accents(input_str):
    """ Remove accents in utf-8 strings
    """
    nfkd_form = unicodedata.normalize('NFKD', input_str)
    return u"".join([c for c in nfkd_form if not unicodedata.combining(c)])


def build_deviceType_from_packageJson(zmq, dev_type_id, client_id):
    result = {}
    status = True
    reason = ""
    # request the packagejson from manager
    cli = MQSyncReq(zmq)
    msg = MQMessage()
    msg.set_action('device_types.get')
    msg.add_data('device_type', dev_type_id)
    res = cli.request('manager', msg.get(), timeout=10)
    del cli
    if res is None:
        status = False
        reason = "Manager is not replying to the mq request"
    if status:
        pjson = res.get_data()
        if pjson is None:
            status = False
            reason = "No data for {0} found by manager".format(dev_type_id)
    if status:
        pjson = pjson[dev_type_id]
        if pjson is None:
            status = False
            reason = "The json for {0} found by manager is empty".format(dev_type_id)
    if status:
        # build the device params
        stats = []
        result['device_type'] = dev_type_id
        result['client_id'] = client_id
        result['name'] = ""
        result['reference'] = ""
        result['description'] = ""
        # append the global xpl and on-xpl params
        result['xpl'] = []
        result['global'] = []
        for param in pjson['device_types'][dev_type_id]['parameters']:
            if param['xpl']:
                del param['xpl']
                result['xpl'].append(param)
            else:
                del param['xpl']
                result['global'].append(param)
        # find the xplCommands
        result['xpl_commands'] = {}
        for cmdn in pjson['device_types'][dev_type_id]['commands']:
            cmd = pjson['commands'][cmdn]
            if 'xpl_command'in cmd:
                xcmdn = cmd['xpl_command']
                xcmd = pjson['xpl_commands'][xcmdn]
                result['xpl_commands'][xcmdn] = []
                stats.append( xcmd['xplstat_name'] )
                for param in xcmd['parameters']['device']:
                    result['xpl_commands'][xcmdn].append(param)
        # find the xplStats
        sensors = pjson['device_types'][dev_type_id]['sensors']
        #print("SENSORS = {0}".format(sensors))
        for xstatn in pjson['xpl_stats']:
            #print("XSTATN = {0}".format(xstatn))
            xstat = pjson['xpl_stats'][xstatn]
            for sparam in xstat['parameters']['dynamic']:
                #print("XSTATN = {0}, SPARAM = {1}".format(xstatn, sparam))
                #if 'sensor' in sparam and xstatn in sensors:
                # => This condition was used to fix a bug which occurs while creating complexe devices for rfxcom
                #    But is introduced a bug for the geoloc plugin...
                #    In fact we had to fix the rfxcom info.json file (open_close uses now rssi_open_close instead of
                #    rssi_lighting2
                #    So, this one is NOT the good one.
                if 'sensor' in sparam:
                # => this condition was the original one restored to make the geoloc pluin ok for tests
                #    Strangely, there is no issue while using the admin (which uses only mq)
                #    but is sucks with test library which uses rest...
                #    This one is the good one
                    if sparam['sensor'] in sensors:
                        #print("ADD")
                        stats.append(xstatn)
        result['xpl_stats'] = {}
        #print("STATS = {0}".format(stats))
        for xstatn in stats:
            xstat = pjson['xpl_stats'][xstatn]
            result['xpl_stats'][xstatn] = []
            for param in xstat['parameters']['device']:
                result['xpl_stats'][xstatn].append(param)
    return (result, reason, status)

if __name__ == "__main__":
    print(get_seconds_since_midnight())
    print(get_midnight_timestamp())
