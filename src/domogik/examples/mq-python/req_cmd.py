#!/usr/bin/python
"""
@api {REQ} cmd.send Send a command (to a client)
@apiVersion 0.4.0
@apiName cmd.send
@apiGroup Command
@apiDescription This request is used by users interfaces to send commands to the clients over the MQ
* Source client : Any user itnerface
* Target client : xplgw

@apiExample {python} Example usage:
    cli = MQSyncReq(zmq.Context())
    msg = MQMessage()
    msg.set_action('cmd.send')
    msg.add_data('cmdid', 6)
    msg.add_data('cmdparams', {"command" : 1})
    return cli.request('xplgw', msg.get(), timeout=10).get()


@apiSuccessExample {json} Success-Response:
[
    'cmd.send.result',
    '{
        "status" : true,
        "reason" : null,
        "uuid" : "8a09462a-4d02-40fd-bf67-4c19240bfbdd"
    }'
]
"""

import zmq
from zmq.eventloop.ioloop import IOLoop
from domogikmq.reqrep.client import MQSyncReq
from domogikmq.message import MQMessage

cli = MQSyncReq(zmq.Context())
msg = MQMessage()
msg.set_action('cmd.send')
msg.add_data('cmdid', 6)
msg.add_data('cmdparams', {"command" : 1})
print cli.request('xplgw', msg.get(), timeout=10).get()
