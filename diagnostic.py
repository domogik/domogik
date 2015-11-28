#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Diagnostic script for Domogik
#

import tempfile
import traceback
import os
import linux_metrics
import socket

FILE=os.path.join(tempfile.gettempdir(), "domogik_diagnostic.log")

# LOG FUNCTIONS
#######################################################################################################

is_warning = False
is_error = False

def title(msg):
    print(u"===========================================================")
    print(u"   {0}".format(msg))
    print(u"===========================================================")

def ok(msg):
    print(u"OK       : {0}".format(msg))

def info(msg):
    print(u"INFO     : {0}".format(msg))

def warning(msg):
    print(u"WARNING  : {0}".format(msg))
    is_warning = True

def error(msg):
    print(u"ERROR    : {0}".format(msg))
    is_error = True

def solution(msg):
    print(u"SOLUTION : {0}".format(msg))


# SERVER RELATED FUNCTIONS
#######################################################################################################

def get_current_metrics():
    info("System informations :")
    cpu_data = linux_metrics.cpu_stat.cpu_info()
    info("- cpu - model          : {0}".format(cpu_data['model name']))
    info("- cpu - num processors : {0}".format(cpu_data['processor_count']))
    info("- cpu - num cores      : {0}".format(cpu_data['cpu cores']))
    num_cores = cpu_data['cpu cores']

    info("System usage :")
    cpu_info = linux_metrics.cpu_stat.cpu_percents()
    info("- cpu (idle)           : {0}".format(cpu_info['idle']))
    info("- cpu (system)         : {0}".format(cpu_info['system']))
    info("- cpu (user)           : {0}".format(cpu_info['user']))
    info("- cpu (iowait)         : {0}".format(cpu_info['iowait']))

    load_avg = linux_metrics.cpu_stat.load_avg()
    info("- load average         : {0} / {1} / {2}".format(load_avg[0], load_avg[1], load_avg[2]))
    load_warn = False
    if load_avg[0] > num_cores:
        warning("The system load is important")
        load_warn = True
    if not load_warn and load_avg[1] > num_cores:
        warning("The system load is important")
        load_warn = True
    if not load_warn and load_avg[2] > num_cores:
        warning("The system load is important")
        load_warn = True
    if not load_warn:
        ok("System load is ok")
   
    mem = linux_metrics.mem_stat.mem_stats()
    used, total, _, _, _, _ = mem
    used = used/(1024*1024)
    total = total/(1024*1024)
    info("- memory - total (Mb)  : {0}".format(total))
    info("- memory - used (Mb)   : {0}".format(used))

    if total < 900:
        error("Domogik needs at least 1Gb of memory on the system to run")
    elif total < 1800:
        warning("Your system have less than 2Gb of memory. Depending of what is already installed on your server, it may not be enough")
    else:
        ok("There is enough memory on the system (if others applications does not use all of it!)")

    if total - used < 100:
        warning("There is less than 100Mb of memory free.")

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
    #print(test_a_port("192.68.1.10", 40406))
    pass

def test_a_port(ip, port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex((ip, port))
    if result == 0:
       return True
    else:
       return False

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
    # System informations
    title("System informations")
    get_current_metrics()

    # Domogik package and configuration
    title("Domogik installations checks")
    test_import_domogik()
    get_install_path()
    test_config_files()

    # Ports
    title("Domogik web services up ?")
    test_ports_are_open()
    
    # MQ
    title("Domogik Message Queue (MQ) checks")
    test_mq_mmi_services()  # test broker services
    test_mq_pubsub()

    # Summary
    title("Summary")
    if is_warning:
        print(u"There were some warnings !")
    if is_error:
        print(u"There were some errors !")
    if not is_warning and not is_error:
        print(u"All seems OK")
