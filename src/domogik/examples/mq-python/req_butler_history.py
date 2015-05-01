#!/usr/bin/python
"""
@api {REQ} butler.history.get Request to get the butler history
@apiVersion 0.4.1
@apiName butler.history.get
@apiGroup Butler
@apiDescription This request is used to ask Domogik's Butler all the N last exchanges
* Source client : Domogik admin, any other interface which can manage the clients
* Target client : always 'butler' 

@apiExample {python} Example usage:
    cli = MQSyncReq(zmq.Context())
    msg = MQMessage()
    msg.set_action('butler.history.get')
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
msg.set_action('butler.history.get')
print(cli.request('butler', msg.get(), timeout=10).get())


