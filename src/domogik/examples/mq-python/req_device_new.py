#!/usr/bin/python
"""
@api {REQ} device.new.get Get the list of the newly detected devices
@apiVersion 0.4.0
@apiName device.new.get
@apiGroup Devices
@apiDescription This request is used to ask a Domogik client (plugin for example) the list of the new devices the client has detected (and that are not already created as Domogik devices).
* Source client : Domogik admin, any other interface which can manage the clients
* Target client : always a client : <type>-<name>.<host>. For example : plugin-rfxcom.darkstar

@apiExample {python} Example usage:
    cli = MQSyncReq(zmq.Context())
    msg = MQMessage()
    msg.set_action('device.new.get')
    print(cli.request('plugin-rfxcom.darkstar', msg.get(), timeout=10).get())
    
@apiSuccessExample {json} Success-Response:
[
]
"""

import zmq
from zmq.eventloop.ioloop import IOLoop
from domogikmq.reqrep.client import MQSyncReq
from domogikmq.message import MQMessage

cli = MQSyncReq(zmq.Context())
msg = MQMessage()
msg.set_action('device.new.get')
print(cli.request('plugin-rfxcom.darkstar', msg.get(), timeout=10).get())

