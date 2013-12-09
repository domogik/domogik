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

from socket import gethostname
#from exceptions import ImportError, AttributeError
from subprocess import Popen, PIPE
import os
import sys
from netifaces import interfaces, ifaddresses, AF_INET, AF_INET6

# used by is_already_launched
STARTED_BY_MANAGER = "NOTICE=THIS_PLUGIN_IS_STARTED_BY_THE_MANAGER"

def get_interfaces():
    return interfaces()

def get_ip_for_interfaces(interface_list=[], ip_type=AF_INET):
    """ Returns all ips that are available for the interfaces in the list
    @param interface_list: a list of interfaces to ge the ips for,
        if the list is empty it will retrun all ips for this system
    @param ip_type: what ip type to get, can be
        AF_INET: for ipv4
        AF_INET6: for ipv6
    @return: a list of ips
    """
    if type(interface_list) is not list:
        assert "The interface_list should be a list"
    if len(interface_list) == 0:
        interface_list = interfaces()
    ips = []
    for intf in interface_list:
        if intf in interfaces():
            for addr in ifaddresses(intf)[ip_type]:
                ips.append(addr['addr'])
        else:
            assert "Interface {0} does not exist".format(intf)
    return ips

def get_sanitized_hostname():
    """ Get the sanitized hostname of the host 
    This will lower it and keep only the part before the first dot
    """
    return gethostname().lower().split('.')[0].replace('-','')[0:16]

def ucode(my_string):
    """Convert a string into unicode or return None if None value is passed

    @param my_string : string value to convert
    @return a unicode string

    """
    if my_string is not None:
        if type(my_string) == unicode:
            return my_string
        elif not type(my_string) == str:
            return str(my_string).decode("utf-8")
        else:
            return my_string.decode("utf-8")
    else:
        return None

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

def is_already_launched(log, id, manager=True):
    """ Check if there are already some process for the component launched
        @param log : logger
        @param id : plugin id to check with pgrep
        @param manager : do we need to find the STARTED_BY_MANAGER String?
        @return : is_launched : True/False
                  pid_list : list of the already launched processes pid
    """
    my_pid = os.getpid()
 
    # the manager add the STARTED_BY_MANAGER useless command to allow the plugin to ignore this command line when it checks if it is already laucnehd or not
    # the final 'grep -v sudo' is here to exclude the lines launched by sudo from the search : using sudo make 2 results be in the grep result : one with sudo and the other one with the command (but this second one is filtered thanks to its pid)
    if manager:
        cmd = "pgrep -lf {0} | grep -v {1} | grep python | grep -v pgrep | grep -v {2} | grep -v sudo | grep -v su".format(id, STARTED_BY_MANAGER, my_pid)
        print "is manager"
    else:
        cmd = "ps aux | grep {0} | grep python | grep -v ps | grep -v sudo | grep -v su".format(id)
    # the grep python is needed to avoid a plugin to not start because someone is editing the plugin with vi :)
    
    if log:
        log.info("Looking for launched instances of '{0}'".format(id))
    is_launched = False
    subp = Popen(cmd, shell=True, stdout=PIPE)
    pid_list = []
    for line in subp.stdout:
        is_launched = True
        if log:
            log.info("Process found : {0}".format(line.rstrip("\n")))
        pid_list.append(line.rstrip("\n").split(" ")[0])
    subp.wait()  
    if is_launched:
        if log:
            log.info("There are already existing processes.")
    else:
        if log:
            log.info("No existing process.")
    return is_launched, pid_list


