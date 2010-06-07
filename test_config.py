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

Module purpose
==============

Test domogik configuration

Implements
==========


@author: Maxence Dunnewind <maxence@dunnewind.net>
@copyright: (C) 2007-2009 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

import os
import sys
from multiprocessing import Process, Pipe
from socket import gethostbyname

BLUE = '\033[94m'
OK = '\033[92m'
WARNING = '\033[93m'
FAIL = '\033[91m'
ENDC = '\033[0m'

def info(msg):
    print "%s [ %s ] %s" % (BLUE,msg,ENDC)
def ok(msg):
    print "%s ==> %s  %s" % (OK,msg,ENDC)
def warning(msg):
    print "%s ==> %s  %s" % (WARNING,msg,ENDC)
def fail(msg):
    print "%s ==> %s  %s" % (FAIL,msg,ENDC)

def am_i_root():
    info("Check this script is started as root")
    assert os.getuid() == 0, "This script must be started as root"
    ok("Correctly started with root privileges.")

def test_imports():
    good = True
    info("Test imports")
    try:
        import domogik
    except ImportError:
        warning("domogik package can not be imported, did you made ./setup.py develop or ./setup.py install ?")
        good = False
    try:
        import OpenSSL
    except ImportError:
        warning("OpenSSL can't be imported, please exec ./setup.py develop or ./setup.py install and check it \
                downloads and install pyOpenSSL correctly.")
        good = False
    try:
        import django
    except ImportError:
        warning("Can't import django, please install it by hand (>= 1.1) or exec ./setup.py develop or ./setup.py install")
        good = False
    try:
        import sqlite3
    except ImportError:
        warning("Can't import sqlite3, please install it by hand (>= 1.1) or exec ./setup.py develop or ./setup.py install")
        good = False
    try:
        import httplib
    except ImportError:
        warning("Can't import httplib, please install it by hand (>= 2) or exec ./setup.py develop or ./setup.py install")
        good = False
    try:
        import simplejson
    except ImportError:
        warning("Can't import simplejson, please install it by hand (>= 1.1) or exec ./setup.py develop or ./setup.py install")
        good = False
    assert good, "One or more import have failed, please install required packages and restart this script."
    ok("Imports are good")

def test_config_files():
    info("Test global config file")
    assert os.path.isfile("/etc/conf.d/domogik") or os.path.isfile("/etc/default/domogik"), \
            "No global config file found, please take src/domogik/examples/default/domogik \
            on your domogik repository and put it on /etc/default/domogik or /etc/conf.d/domogik \
            (depending of your system)."
    assert not (os.path.isfile("/etc/conf.d/domogik") and os.path.isfile("/etc/default/domogik")), \
            "Global config file found at 2 locations. Please put it only at /etc/default/domogik or \
            /etc/conf.d/domogik."
    if os.path.isfile("/etc/default/domogik"):
        file = "/etc/default/domogik"
    else:
        file = "/etc/conf.d/domogik"
    f = open(file,"r")
    r = f.readlines()
    lines = filter(lambda x: not x.startswith('#') and x != '\n',r)
    f.close()
    user = ''
    manager_params = ''
    custom_path = ''
    for line in lines:
        item,value = line.strip().split("=")
        if item.strip() == "DOMOGIK_USER":
            user = value
        elif item.strip() == "MANAGER_PARAMS":
            manager_params = value
        elif item.strip() == "CUSTOM_PATH":
            custom_path = value
        else:
            warning("Unknown config value in the main config file : %s" % item)
    ok("Global config file exists and contains right stuff")

    #Check manager params
    info("Check manager params")
    params = True
    if "-d" not in manager_params:
        warning("No -d option in MANAGER_PARAMS. You should have it unless you are using domogik on more than one computer.")
        params = False
    if "-r" not in manager_params:
        warning("No -r option in MANAGER_PARAMS. You should have it unless you are using domogik on more than one computer.")
        params = False
    if params:
        ok("Manager params seem good")

    #Check if we can find xPL_Hub
    info("Check xPL_Hub is in path")
    path = os.environ['PATH'].split(':')
    path.append(custom_path)
    l = [p for p in path if os.path.exists(os.path.join(p, 'xPL_Hub'))]
    assert l != [], "xPL_Hub can't be found, please double check CUSTOM_PATH is correctly defined."
    ok("xPL_Hub found in the path")
    
    info("Test user / config file")

    #Check user config file
    import pwd
    try:
        user_entry = pwd.getpwnam(user)
    except KeyError:
        raise KeyError("The user %s does not exists, you MUST create it or change the DOMOGIK_USER parameter in %s" % (user, file))
    user_home = user_entry.pw_dir
    assert os.path.isfile("%s/.domogik.cfg" % user_home), "The domogik config file %s/.domogik does not exists. \
            Please copy it from src/domogik/examples/config/domogik and update it." % user_home
    ok("Domogik's user exists and has a config file")
    
    test_user_config_file(user_home, user_entry)

def _test_user_can_write(conn, path, user_entry):
    os.setgid(user_entry.pw_gid)
    os.setuid(user_entry.pw_uid)
    conn.send(os.access(path, os.W_OK))
    conn.close()

def _check_port_availability(s_ip, s_port):
    """ Parse /proc/net/tcp to check if something listen on the port"""
    ip = gethostbyname(s_ip).split('.')
    port = "%04X" % int(s_port)
    ip = "%02X%02X%02X%02X" % (int(ip[3]),int(ip[2]),int(ip[1]),int(ip[0]))
    f = open("/proc/net/tcp")
    lines = f.readlines()
    f.close()
    lines.pop(0)
    for line in lines:
        data = line.split()
        d_ip = data[1].split(':')[0]
        d_port = data[1].split(':')[1]
        if d_port == port:
            assert d_ip != ip and ip != "00000000", "A service already listen on ip %s and port %s." % (s_ip, s_port)

def test_user_config_file(user_home, user_entry):
    info("Check user config file contents")
    import ConfigParser
    config = ConfigParser.ConfigParser()
    config.read("%s/.domogik.cfg" % user_home)
    
    #check [domogik] section
    dmg = dict(config.items('domogik'))
    database = dict(config.items('database'))
    rest = dict(config.items('rest'))
    ok("Config file correctly loaded")

    info("Parse [domogik] section")
    import domogik

    parent_conn, child_conn = Pipe()
    p = Process(target=_test_user_can_write, args=(child_conn, dmg['log_dir_path'],user_entry,))
    p.start()
    p.join()
    assert parent_conn.recv(), "The directory %s for log does not exist or does not have right permissions" % dmg['log_dir_path']

    assert dmg['log_level'] in ['debug','info','warning','error','critical'], "The log_level parameter does not have a good value. Must \
            be one of debug,info,warning,error,critical"
    assert domogik.__path__[0].startswith(dmg['custom_prefix']), "Custom prefix parameter is wrong, it must be the prefix of your domogik install.\
            If you have installed domogik with ./setup.py develop, you should be able to get it by taping in a python console :\n\
            import os,domogik\n\
            print os.path.dirname(domogik.__path__[0])"
    ok("[domogik] section seems good")

    # check [database] section
    info("Parse [database] section")
    assert database['db_type'] == 'sqlite', "Only sqlite database type is supported at the moment"

    parent_conn, child_conn = Pipe()
    p = Process(target=_test_user_can_write, args=(child_conn, database['db_path'] ,user_entry,))
    p.start()
    p.join()
    assert parent_conn.recv(), "The database file does not exists or domogik user can't write on it. \
                Did you exec db_installer.py ?\n\
                Are you sure you have define the full path, including filename, without ~ ?"
    ok("[database] section seems good")
    
    # Check [rest] section
    info("Parse [rest] section")
    _check_port_availability(rest['rest_server_ip'], rest['rest_server_port'])
    ok("Rest server IP/port is not bound by anything else")
    _check_port_availability(rest['django_server_ip'], rest['django_server_port'])
    ok("Django server IP/port is not bound by anything else")

def test_init():
    info("Check init.d / rc.d")
    assert os.access("/etc/init.d/domogik", os.X_OK) or os.access("/etc/rc.d/domogik", os.X_OK), "/etc/init.d/domogik and /etc/rc.d/domogik do not \
            exist or can't be executed.\
            Please copy src/domogik/examples/init/domogik to /etc/init.d or /etc/rc.d depending on your system, and chmod +x /etc/init.d/domogik"
    ok("/etc/init.d/domogik or /etc/rc.d/domogik found with good permissions")

def test_version():
    info("Check python version")
    v = sys.version_info()
    assert v[0] == 2 and v[1] < 6, "Python version is %s.%s, it must be >= 2.6, please upgrade" % (v[0], v[1])
    ok("Python version is >= 2.6")

try:
    am_i_root()
    test_imports()
    test_config_files()
    test_init()
    test_version()
    print "\n\n"
    ok("================================================== <==")
    ok(" Everything seems ok, you should be able to start  <==")
    ok("      Domogik with /etc/init.d/domogik start       <==")
    ok("            or /etc/rc.d/domogik start             <==")
    ok("================================================== <==")
except:
    fail(sys.exc_info()[1])

