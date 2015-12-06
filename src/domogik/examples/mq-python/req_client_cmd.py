#!/usr/bin/python
"""
@api {REQ} client.cmd send a command to a client
@apiVersion 0.4.0
@apiName client.cmd
@apiGroup Command
@apiDescription This request is used by the clientGw to forward a command to the correct plugin
* Source client : ClientGw
* Target client : Any plugin

@apiExample {python} Example usage:
    cli = MQSyncReq(zmq.Context())
    msg = MQMessage()
    msg.set_action('client.command')
    msg.add_data('command_id', 6)
    msg.add_data('device_id', 6)
    msg.add_data('param1', 1)
    msg.add_data('param2', 2)
    return cli.request('igor.velbus', msg.get(), timeout=10).get()


@apiSuccessExample {json} Success-Response:
[
    'client.command.response',
    '{
        "status" : true,
        "reason" : null,
    }'
]
"""

import zmq
from zmq.eventloop.ioloop import IOLoop
from domogikmq.reqrep.client import MQSyncReq
from domogikmq.message import MQMessage

cli = MQSyncReq(zmq.Context())
msg = MQMessage()
msg.set_action('client.cmd')
msg.add_data('command_id', 6)
msg.add_data('device_id', 6)
msg.add_data('param1', 1)
msg.add_data('param2', 2)
print cli.request('igor.velbus', msg.get(), timeout=10).get()
