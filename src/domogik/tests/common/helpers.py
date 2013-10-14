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

Purpose
=======

Tools for regression tests

Usage
=====

@author: Fritz SMH <fritz.smh@gmail.com> 
@copyright: (C) 2007-2012 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

import zmq
from zmq.eventloop.ioloop import IOLoop
from domogik.common.configloader import Loader
from domogik.common.utils import get_ip_for_interfaces
from domogik.mq.reqrep.client import MQSyncReq
from domogik.mq.message import MQMessage



### Common features

def ask(question):
    """ Ask the suer for something and return True (y/Y) or False (n/N)
        @param question : question displayed
    """

    while True:
        print("{0}\n[yes/no]".format(question))
        # raw_input returns the empty string for "enter"
        yes = set(['yes','y', 'ye'])
        no = set(['no','n'])
        
        choice = raw_input().lower()
        if choice in yes:
           return True
        elif choice in no:
           return False
        else:
           print("Please respond with 'yes' or 'no'")


### Domogik general checks

def check_domogik_is_running():
    """ a function to check if domogik is running, and so if the tests can be done
    """
    # currently, we only ask the user to check
    return ask("Notice that the plugin configuration will be reset for the tests!\nTests should only be done on dedicated environments!!!!!!!!!! Check that Domogik is up and.... are you ready ?")
    

def get_rest_url():
    """ Return the REST server url (constructed from the configuration file of the host)
    """
    cfg = Loader('rest')
    config = cfg.load()
    conf = dict(config[1])
    # we return the url related to the first declared interface in domogik.cfg
    print conf
    intf = conf['interfaces'].split(",")[0]
    ip = get_ip_for_interfaces([intf])[0]
    return "http://{0}:{1}/".format(ip, conf['port'])

### Plugin configuration features

def delete_configuration(type, name, host):
    cli = MQSyncReq(zmq.Context())
    msg = MQMessage()
    msg.set_action('config.delete')
    msg.add_data('type', type)
    msg.add_data('host', host)
    msg.add_data('name', name)
    result = cli.request('dbmgr', msg.get(), timeout=10)
    if result:
        print(result.get())
        return True
    else:
        raise RuntimeError("Timeout while deleting configuration for {0}-{1}.{2}".format(type, name, host))

def configure(type, name, host, key, value):
    cli = MQSyncReq(zmq.Context())
    msg = MQMessage()
    msg.set_action('config.set')
    msg.add_data('type', type)
    msg.add_data('host', host)
    msg.add_data('name', name)
    msg.add_data('data', {key : value})
    result = cli.request('dbmgr', msg.get(), timeout=10)
    if result:
        print(result.get())
        return True
    else:
        raise RuntimeError("Error while setting configuration for {0}-{1}.{2} : {3} = {4}".format(type, name, host, key, value))

