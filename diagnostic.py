#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Diagnostic script for Domogik
#

import tempfile
import traceback
import os

FILE=os.path.join(tempfile.gettempdir(), "domogik_diagnostic.log")

# LOG FUNCTIONS
#######################################################################################################

def ok(msg):
    print(u"OK : {0}".format(msg))

def info(msg):
    print(u"INFO : {0}".format(msg))

def warning(msg):
    print(u"WARNING : {0}".format(msg))

def error(msg):
    print(u"ERROR : {0}".format(msg))

def solution(msg):
    print(u"SOLUTION : {0}".format(msg))


# UTIL FUNCTIONS
#######################################################################################################

def get_install_path():
    try:
        import domogik
        path = domogik.__path__[0]
        getParentFolder = lambda fh: os.path.abspath(os.path.join(os.path.normpath(fh),os.path.pardir))
        return getParentFolder(getParentFolder(path))
    except:
        error("Error while getting domogik module path : {0}".format(traceback.format_exc()))
        return None




# BASIC TESTS
#######################################################################################################

def test_import_domogik():
    try:
        import domogik
        ok("Domogik module can be imported")
        return True
    except:
        error("Error while importing domogik module")
        solution("Make sure the Domogik installation is OK")
        return False


def test_config_files():
    # TODO : /etc/default

    ### /etc/domogik/domogik.cfg
    from domogik.common.configloader import Loader, CONFIG_FILE
    try:
        cfg = Loader('domogik')
        config = cfg.load()
        conf = dict(config[1])

        ok("Configuration file '{0}' can be read".format(CONFIG_FILE))
        return True
    except:
        error(u"Error while reading the configuration file '{0}' : {1}".format(CONFIG_FILE, traceback.format_exc()))
        solution("Make sure the Domogik installation is OK")
        return False
 

def test_free_disk_space():
    # TODO
    pass

def test_total_memory():
    # TODO
    pass

def test_load_average():
    # TODO
    pass

def test_grants():
    # TODO
    # - get the domogik user
    # - check all files have the grants
    # - check /var/log/domogik
    # - check /var/run/domogik
    pass


# PORT TESTS
#######################################################################################################

def test_ports_are_open():
    # TODO
    pass

# XPL TEST
#######################################################################################################

def is_hub_alive():
    # TODO
    pass

def send_xpl_and_get_it():
    # TODO : 
    # - launch dmg_dump in a thread for 30 seconds and log in a file
    # - use dmg_send to send a xpl message
    # - check in dmg_dump logs id the xpl message was sent
    pass


# MQ TESTS - GLOBAL
#######################################################################################################

def test_pubsub():
    # TODO
    # - subscribe
    # - publish
    # - check we got the MQ msg
    pass

def test_reqrep():
    # TODO : 
    # - in a thread wait for some req and do the rep
    # - do the req
    # - chekc we get the rep
    pass
    

# MQ TESTS - SOME DOMOGIK MESSAGE WHILE DOMOGIK IS RUNNING
#######################################################################################################

def test_clients_list():
    # TODO
    # request the clients list and check core are not dead
    pass



# ADVANCED TESTS
#######################################################################################################

def test_plugin():
    # TODO
    # - install the domogik-plugin-test
    # - launch its tests
    pass



# LAUNCH TESTS
#######################################################################################################

if __name__ == "__main__":
    test_import_domogik()
    test_config_files()
    print(get_install_path())
