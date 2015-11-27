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
    print(u"OK       : {0}".format(msg))

def info(msg):
    print(u"INFO     : {0}".format(msg))

def warning(msg):
    print(u"WARNING  : {0}".format(msg))

def error(msg):
    print(u"ERROR    : {0}".format(msg))

def solution(msg):
    print(u"SOLUTION : {0}".format(msg))


# UTIL FUNCTIONS
#######################################################################################################

def get_install_path():
    try:
        import domogik
        path = domogik.__path__[0]
        getParentFolder = lambda fh: os.path.abspath(os.path.join(os.path.normpath(fh),os.path.pardir))
        pp = getParentFolder(getParentFolder(path))
        info(u"Install path : {0}".format(pp))
        return pp
    except:
        error("Error while getting domogik module path : {0}".format(traceback.format_exc()))
        return None




# BASIC TESTS
#######################################################################################################

def test_import_domogik():
    try:
        import domogik
        ver = domogik.__version__
        ok("Domogik module can be imported (version is {0})".format(ver))
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

def test_mq_mmi_services():
    # Test the broker services

    import zmq
    from zmq.eventloop.ioloop import IOLoop
    from domogikmq.reqrep.client import MQSyncReq
    from domogikmq.message import MQMessage
    cli = MQSyncReq(zmq.Context())
    info("Looking for MQ mmi services (broker)")
    res = cli.rawrequest('mmi.services', '', timeout=10)
    if res == None:
        error("No response from MQ mmi.services request : MQ req/rep is KO")
        return
    info("MQ mmi services response is : {0}".format(res))
    components = res[0].replace(" ", "").split(",")
    for core in ['manager', 'dbmgr', 'admin', 'scenario', 'butler', 'xplgw']:
        if core in components:
            ok("MQ rep/req service OK for component : {0}".format(core))
        else:
            error("MQ rep/req service KO for component : {0}".format(core))

def test_mq_pubsub():
    # TODO
    # - subscribe
    # - publish
    # - check we got the MQ msg

    info("If this is the last line displayed, there is an issue with MQ pub/sub : no plugin.status message is received from Domogik. If so, please check Domogik is up and runnin before launching the diagnostic script")
    import zmq
    from domogikmq.pubsub.subscriber import MQSyncSub

    # test subscription is OK
    class TestMQSub(MQSyncSub):

        def __init__(self):
            MQSyncSub.__init__(self, zmq.Context(), 'diag', ['plugin.status'])
            try:
                msg = self.wait_for_event()
                if "content" in msg:
                    ok("MQ : plugin.status message received. MS pub/sub is working")
                else:
                    warning("MQ : plugin.status message received but the content is not good")
            except:
                error("Error while waiting for a domogik component MQ status message. Error is : {0}".format(traceback.format_exc()))

    t = TestMQSub()

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
    get_install_path()
    test_config_files()

    # MQ
    test_mq_mmi_services()  # test broker services
    test_mq_pubsub()
