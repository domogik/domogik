#!/usr/bin/python
# -*- coding: utf-8 -*-                                                                           
"""
@api {SUB} plugin.status Subscribe to the updates of the plugins status
@apiVersion 0.4.0
@apiName plugin.status
@apiGroup Plugin
@apiDescription Subscribe to the updates of the plugins status (alive, stopped, ...)
* Source client : Domogik admin, any other interface which can need to get the plugins status informations
* Target client : n/a (any publisher)

@apiExample {python} Example usage:
     class Test(MQAsyncSub):
     
         def __init__(self):
             MQAsyncSub.__init__(self, zmq.Context(), 'test', ['plugin.status'])
             IOLoop.instance().start()
     
         def on_message(self, msgid, content):
             print(u"New pub message {0}".format(msgid))
             print(u"{0}".format(content))
    
    if __name__ == "__main__":
        Test()
    
@apiSuccessExample {json} Success-Response:
{
    u'host': u'darkstar',
    u'type': u'plugin',
    u'name': u'teleinfo',
    u'event': u'starting'
}
"""

import zmq
from domogikmq.pubsub.subscriber import MQAsyncSub
from zmq.eventloop.ioloop import IOLoop
from domogikmq.message import MQMessage

class Test(MQAsyncSub):

    def __init__(self):
        MQAsyncSub.__init__(self, zmq.Context(), 'test', ['plugin.status'])
        IOLoop.instance().start()

    def on_message(self, msgid, content):
        print(u"New pub message {0}".format(msgid))
        print(u"{0}".format(content))

if __name__ == "__main__":
    Test()
