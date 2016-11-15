#!/usr/bin/python
# -*- coding: utf-8 -*-                                                                           
"""
@api {SUB} client.sensor Subscribe to the sensor data
@apiVersion 0.4.0
@apiName client.sensor
@apiGroup Client
@apiDescription Subscribe to new sensor values
* Source client : Any plugin
* Target client : Domogik xplgw
This is a key/value pair, where the key is the sensorId and the value is the value to store.
Optional we can add an atTimestamp key, if this key is pressent we will use the value as the 
time to be stored in the db, otherwise the current timestamp will be used

@apiExample {python} Example usage:
     class Test(MQAsyncSub):
     
         def __init__(self):
             MQAsyncSub.__init__(self, zmq.Context(), 'test', ['client.sensor'])
             IOLoop.instance().start()
     
         def on_message(self, msgid, content):
             print(u"New pub message {0}".format(msgid))
             print(u"{0}".format(content))
    
    if __name__ == "__main__":
        Test()
    
@apiSuccessExample {json} Success-Response:
{
    u'251' : 20.5,
    u'255' : 23
    u'atTimestamp' : 234567
}
"""

import zmq
from domogikmq.pubsub.subscriber import MQAsyncSub
from zmq.eventloop.ioloop import IOLoop
from domogikmq.message import MQMessage

class Test(MQAsyncSub):

    def __init__(self):
        MQAsyncSub.__init__(self, zmq.Context(), 'test', ['client.sensor'])
        IOLoop.instance().start()

    def on_message(self, msgid, content):
        print(u"New pub message {0}".format(msgid))
        print(u"{0}".format(content))

if __name__ == "__main__":
    Test()
