#!/usr/bin/python
"""
@api {REQ} butler.scripts.get Request to get all the scripts handled by the butler
@apiVersion 0.4.1
@apiName butler.scripts.get
@apiGroup Butler
@apiDescription This request is used to ask Domogik's Butler all the loaded scripts for the current language.
* Source client : Domogik admin, any other interface which can manage the clients
* Target client : always 'butler' 

@apiExample {python} Example usage:
    cli = MQSyncReq(zmq.Context())
    msg = MQMessage()
    msg.set_action('butler.scripts.get')
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
msg.set_action('butler.scripts.get')
print(cli.request('butler', msg.get(), timeout=10).get())


