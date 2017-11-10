#!/usr/bin/python
# -*- coding: utf-8 -*-                                                                           
"""
@api {SUB} client.conversion Subscribe to the updates of the conversion functions of the clients
@apiVersion 0.4.0
@apiName client.conversion
@apiGroup Client
@apiDescription Subscribe to the updates of the conversion functions of the clients
* Source client : Mainly the xplgw component to be able to convert the received data when conversion functions exist.
* Target client : n/a (any publisher)

@apiExample {python} Example usage:
     class Test(MQAsyncSub):
     
        def __init__(self):
            MQAsyncSub.__init__(self, zmq.Context(), 'test', ['client.conversion'])
            IOLoop.instance().start()
     
         def on_message(self, msgid, content):
             print(u"New pub message {0}".format(msgid))
             print(u"{0}".format(content))
    
    if __name__ == "__main__":
        Test()
    
@apiSuccessExample {json} Success-Response:
{
    u'core-scenario.darkstar': None,
    u'core-admin.darkstar': None,
    u'core-xplgw.darkstar': None,
    u'core-rest.darkstar': None,
    u'plugin-diskfree.darkstar': {
        
    },
    u'plugin-teleinfo.darkstar': {
        
    }
}
"""

import zmq
from domogikmq.pubsub.subscriber import MQAsyncSub
from zmq.eventloop.ioloop import IOLoop
from domogikmq.message import MQMessage

class Test(MQAsyncSub):

    def __init__(self):
        MQAsyncSub.__init__(self, zmq.Context(), 'test', ['client.conversion'])
        IOLoop.instance().start()

    def on_message(self, msgid, content):
        print(u"New pub message {0}".format(msgid))
        print(u"{0}".format(content))

if __name__ == "__main__":
    Test()
