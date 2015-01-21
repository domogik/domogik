#!/usr/bin/python
# -*- coding: utf-8 -*-                                                                           
"""
@api {SUB} device-stats Subscribe to newly stored device stats
@apiVersion 0.4.0
@apiName device-stats
@apiGroup Client
@apiDescription Subscribe to newly stored device stats
* Source client : n/a (any subscriber)
* Target client : The xplgw will transmit these messages

@apiExample {python} Example usage:
     class Test(MQAsyncSub):
     
        def __init__(self):
            MQAsyncSub.__init__(self, zmq.Context(), 'test', ['device-stats'])
            IOLoop.instance().start()
     
         def on_message(self, msgid, content):
             print(u"New pub message {0}".format(msgid))
             print(u"{0}".format(content))
    
    if __name__ == "__main__":
        Test()
    
@apiSuccessExample {json} Success-Response:
{
    u'timestamp': 1421415094,
    u'sensor_id': 210,
    u'device_id': 75,
    u'stored_value': u'16.6875'
}
"""

import zmq
from domogikmq.pubsub.subscriber import MQAsyncSub
from zmq.eventloop.ioloop import IOLoop
from domogikmq.message import MQMessage

class Test(MQAsyncSub):

    def __init__(self):
        MQAsyncSub.__init__(self, zmq.Context(), 'test', ['device-stats'])
        IOLoop.instance().start()

    def on_message(self, msgid, content):
        print(u"New pub message {0}".format(msgid))
        print(u"{0}".format(content))

if __name__ == "__main__":
    Test()
