#!/usr/bin/python
"""
@api {REQ} cmd.send Send a command to a Domogik device over the MQ
@apiVersion 0.4.0
@apiName cmd.send
@apiGroup Commands
@apiDescription This request is used to send a command to a Domogik device over the message queue.
* Source client : Any interface which can send commands to a Domogik device
* Target client : always 'xplgw'

@apiExample {python} Example usage:
    cli = MQSyncReq(zmq.Context())
    msg = MQMessage()
    msg.set_action('cmd.send')
    msg.add_data('cmdid', 1)
    msg.add_data('cmdparams', {'level': 0})
    print(cli.request('xplgw', msg.get(), timeout=10).get())
    
@apiParam {String} cmdid The id of a command of a Domogik device (you should first find your device with device.get to get its commands ids
@apiParam {String} cmdparams A dictionnary of the parameters of the command. The list of the parameters is related to the device type of the Domogik device.

@apiSuccessExample {json} Success-Response:
[]
"""

import zmq
from zmq.eventloop.ioloop import IOLoop
from domogikmq.reqrep.client import MQSyncReq
from domogikmq.message import MQMessage

cli = MQSyncReq(zmq.Context())
msg = MQMessage()
msg.set_action('cmd.send')
msg.add_data('cmdid', 1)
msg.add_data('cmdparams', {'level': 0})
print(cli.request('xplgw', msg.get(), timeout=10).get())


