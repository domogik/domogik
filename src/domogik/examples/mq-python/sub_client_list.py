#!/usr/bin/python
# -*- coding: utf-8 -*-                                                                           
"""
@api {SUB} client.list Subscribe to the updates of the list of the available clients.
@apiVersion 0.4.0
@apiName client.list
@apiGroup Client
@apiDescription Subscribe to the updates of the list of the available clients.
* Source client : Domogik admin, any other interface which can need to get the clients status (this can also be a user interface in order to deactivate the widgets for a stopped client).
* Target client : n/a (any publisher)

@apiExample {python} Example usage:
     class Test(MQAsyncSub):
     
         def __init__(self):
             MQAsyncSub.__init__(self, zmq.Context(), 'test', ['client.list'])
             IOLoop.instance().start()
     
         def on_message(self, msgid, content):
             print(u"New pub message {0}".format(msgid))
             print(u"{0}".format(content))
    
    if __name__ == "__main__":
        Test()
    
@apiSuccessExample {json} Success-Response:
{
    u'core-scenario.darkstar': {
        u'status': u'alive',
        u'name': u'scenario',
        u'xpl_source': u'domogik-scenario.darkstar',
        u'configured': None,
        u'pid': 19342,
        u'package_id': u'core-scenario',
        u'host': u'darkstar',
        u'type': u'core',
        u'last_seen': 1412625186.012657
    },
    u'core-admin.darkstar': {
        u'status': u'alive',
        u'name': u'admin',
        u'xpl_source': u'domogik-admin.darkstar',
        u'configured': None,
        u'pid': 19241,
        u'package_id': u'core-admin',
        u'host': u'darkstar',
        u'type': u'core',
        u'last_seen': 1412625183.384482
    },
    u'core-xplgw.darkstar': {
        u'status': u'alive',
        u'name': u'xplgw',
        u'xpl_source': u'domogik-xplgw.darkstar',
        u'configured': None,
        u'pid': 19308,
        u'package_id': u'core-xplgw',
        u'host': u'darkstar',
        u'type': u'core',
        u'last_seen': 1412625185.280722
    },
    u'core-rest.darkstar': {
        u'status': u'alive',
        u'name': u'rest',
        u'xpl_source': u'domogik-rest.darkstar',
        u'configured': None,
        u'pid': 19274,
        u'package_id': u'core-rest',
        u'host': u'darkstar',
        u'type': u'core',
        u'last_seen': 1412625184.411622
    },
    u'plugin-diskfree.darkstar': {
        u'status': u'alive',
        u'name': u'diskfree',
        u'xpl_source': u'domogik-diskfree.darkstar',
        u'configured': True,
        u'pid': 19377,
        u'package_id': u'plugin-diskfree',
        u'host': u'darkstar',
        u'type': u'plugin',
        u'last_seen': 1412625366.473103
    },
    u'plugin-teleinfo.darkstar': {
        u'status': u'unknown',
        u'name': u'teleinfo',
        u'xpl_source': u'domogik-teleinfo.darkstar',
        u'configured': True,
        u'pid': 0,
        u'package_id': u'plugin-teleinfo',
        u'host': u'darkstar',
        u'type': u'plugin',
        u'last_seen': 1412625306.477851
    }
}
"""

import zmq
from domogikmq.pubsub.subscriber import MQAsyncSub
from zmq.eventloop.ioloop import IOLoop
from domogikmq.message import MQMessage

class Test(MQAsyncSub):

    def __init__(self):
        MQAsyncSub.__init__(self, zmq.Context(), 'test', ['client.list'])
        IOLoop.instance().start()

    def on_message(self, msgid, content):
        print(u"New pub message {0}".format(msgid))
        print(u"{0}".format(content))

if __name__ == "__main__":
    Test()
