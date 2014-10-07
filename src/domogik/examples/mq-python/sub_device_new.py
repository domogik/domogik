#!/usr/bin/python
# -*- coding: utf-8 -*-                                                                           
"""
@api {SUB} device.new Subscribe to the updates of newly detected devices for all clients
@apiVersion 0.4.0
@apiName device.new
@apiGroup Client
@apiDescription Subscribe to the updates of the list of the new devices the clients have detected (and that are not already created as Domogik devices).
* Source client : Any interface (admin or other that can let the user to know some new device have been detected.
* Target client : n/a (any publisher)

@apiExample {python} Example usage:
     class Test(MQAsyncSub):
     
        def __init__(self):
            MQAsyncSub.__init__(self, zmq.Context(), 'test', ['device.new'])
            IOLoop.instance().start()
     
         def on_message(self, msgid, content):
             print(u"New pub message {0}".format(msgid))
             print(u"{0}".format(content))
    
    if __name__ == "__main__":
        Test()
    
@apiSuccessExample {json} Success-Response:
{...}
"""

import zmq
from domogikmq.pubsub.subscriber import MQAsyncSub
from zmq.eventloop.ioloop import IOLoop
from domogikmq.message import MQMessage

class Test(MQAsyncSub):

    def __init__(self):
        MQAsyncSub.__init__(self, zmq.Context(), 'test', ['device.new'])
        IOLoop.instance().start()

    def on_message(self, msgid, content):
        print(u"New pub message {0}".format(msgid))
        print(u"{0}".format(content))

if __name__ == "__main__":
    Test()
