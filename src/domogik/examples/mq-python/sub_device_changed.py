#!/usr/bin/python
# -*- coding: utf-8 -*-                                                                           
"""
@api {SUB} device-changed Subscribe to device changes
@apiVersion 0.4.0
@apiName device.update
@apiGroup Client
@apiDescription Subscribe to newly stored device stats
* Source client : n/a (any subscriber)
* Target client : The dbMgr will transmit these messages

@apiExample {python} Example usage:
     class Test(MQAsyncSub):
     
        def __init__(self):
            MQAsyncSub.__init__(self, zmq.Context(), 'test', ['device.update'])
            IOLoop.instance().start()
     
         def on_message(self, msgid, content):
             print(u"New pub message {0}".format(msgid))
             print(u"{0}".format(content))
    
    if __name__ == "__main__":
        Test()
    
@apiSuccessExample {json} Success-Response:
{
    u'device_id': 75,
    u'client_id': u'domogik.velbus-igor'
}
"""

import zmq
from domogikmq.pubsub.subscriber import MQAsyncSub
from zmq.eventloop.ioloop import IOLoop
from domogikmq.message import MQMessage

class Test(MQAsyncSub):

    def __init__(self):
        MQAsyncSub.__init__(self, zmq.Context(), 'test', ['device.update'])
        IOLoop.instance().start()

    def on_message(self, msgid, content):
        print(u"New pub message {0}".format(msgid))
        print(u"{0}".format(content))

if __name__ == "__main__":
    Test()
