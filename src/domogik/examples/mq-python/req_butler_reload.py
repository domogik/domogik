#!/usr/bin/python
"""
@api {REQ} butler.reload.do Request to reload the butler brain parts
@apiVersion 0.4.1
@apiName butler.reload.do
@apiGroup Butler
@apiDescription This request is used to ask Domogik's Butler to reload the brain parts
* Source client : Domogik admin, any other interface which can manage the clients
* Target client : always 'butler' 

@apiExample {python} Example usage:
    cli = MQSyncReq(zmq.Context())
    msg = MQMessage()
    msg.set_action('butler.reload.do')
    print(cli.request('butler', msg.get(), timeout=10).get())

@apiSuccessExample {json} Success-Response:
['butler.reload.result', '{"status": true, "reason": ""}']

@apiErrorExample {json} Error-Response:
['butler.reload.result', '{"status": false, "reason": "some error message"}']
"""

import zmq
from zmq.eventloop.ioloop import IOLoop
from domogikmq.reqrep.client import MQSyncReq
from domogikmq.message import MQMessage

cli = MQSyncReq(zmq.Context())
msg = MQMessage()
msg.set_action('butler.reload.do')
print(cli.request('butler', msg.get(), timeout=10).get())



