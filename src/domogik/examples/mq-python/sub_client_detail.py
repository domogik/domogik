#!/usr/bin/python
# -*- coding: utf-8 -*-                                                                           
"""
@api {SUB} client.detail Subscribe to the updates of the detailed list of the available clients.
@apiVersion 0.4.0
@apiName client.detail
@apiGroup Client
@apiDescription Subscribe to the updates of the list of the available clients.
* Source client : Domogik admin, any other interface which can need to get the clients details.
* Target client : n/a (any publisher)

@apiExample {python} Example usage:
     class Test(MQAsyncSub):
     
        def __init__(self):
            MQAsyncSub.__init__(self, zmq.Context(), 'test', ['client.detail'])
            IOLoop.instance().start()
     
         def on_message(self, msgid, content):
             print(u"New pub message {0}".format(msgid))
             print(u"{0}".format(content))
    
    if __name__ == "__main__":
        Test()
    
@apiSuccessExample {json} Success-Response:
You will get almost the same json as for client.list.
For each client a data key is added with the content of the info.json file of the client.
"""

import zmq
from domogikmq.pubsub.subscriber import MQAsyncSub
from zmq.eventloop.ioloop import IOLoop
from domogikmq.message import MQMessage

class Test(MQAsyncSub):

    def __init__(self):
        MQAsyncSub.__init__(self, zmq.Context(), 'test', ['client.detail'])
        IOLoop.instance().start()

    def on_message(self, msgid, content):
        print(u"New pub message {0}".format(msgid))
        print(u"{0}".format(content))

if __name__ == "__main__":
    Test()
