#!/usr/bin/python
"""
@api {REQ} butler.discuss.do Request to discuss with the butler
@apiVersion 0.5.0
@apiName butler.discuss.do
@apiGroup Butler
@apiDescription This request is used to discuss with the butler (but please use the pub/sub method when possible)
* Source client : Rest url entry point to discuss with the butler
* Target client : always 'butler' 
Be careful, the response may be lon if the butler has some important processing to do or is waiting for a remote server response... The default timeout may not be enough!

@apiExample {python} Example usage:
    cli = MQSyncReq(zmq.Context())
    msg = MQMessage()
    msg.set_action('butler.discuss.do')
    data = {"media" : "audio",
            "location" : None,
            "sex" : None,
            "mood" : None,
            "source" : "a_client",
            "identity" : "someone",
            "text" : "hello"}
    msg.set_data(data)
    print(cli.request('butler', msg.get(), timeout=30).get())

@apiSuccessExample {json} Success-Response:
['butler.discuss.result', '{"mood": null, "media": "audio", "sex": "female", "location": null, "text": "Salut", "reply_to": "a_client", "identity": "Aria"}']

"""

import zmq
from zmq.eventloop.ioloop import IOLoop
from domogikmq.reqrep.client import MQSyncReq
from domogikmq.message import MQMessage

cli = MQSyncReq(zmq.Context())
msg = MQMessage()
msg.set_action('butler.discuss.do')
data = {"media" : "audio",
        "location" : None,
        "sex" : None,
        "mood" : None,
        "source" : "a_client",
        "identity" : "someone",
        "text" : "hello"}
msg.set_data(data)
print(cli.request('butler', msg.get(), timeout=30).get())



