#!/usr/bin/python
"""
@api {REQ} butler.features.get Request to get the butler features
@apiVersion 0.4.1
@apiName butler.features.get
@apiGroup Butler
@apiDescription This request is used to ask Domogik's Butler all the features
* Source client : the core brain package
* Target client : always 'butler' 

@apiExample {python} Example usage:
    cli = MQSyncReq(zmq.Context())
    msg = MQMessage()
    msg.set_action('butler.features.get')
    print(cli.request('butler', msg.get(), timeout=10).get())

@apiSuccessExample {json} Success-Response:
[
    TODO
]
"""

import zmq
from zmq.eventloop.ioloop import IOLoop
from domogikmq.reqrep.client import MQSyncReq
from domogikmq.message import MQMessage

cli = MQSyncReq(zmq.Context())
msg = MQMessage()
msg.set_action('butler.features.get')
print(cli.request('butler', msg.get(), timeout=10).get())


