#!/usr/bin/python
"""
@api {REQ} device.params Get the parameters that are needed to set for creating a Domogik device of a given device type
@apiVersion 0.4.0
@apiName device.params
@apiGroup Devices
@apiDescription This request is used to ask Domogik's admin the list of the params (key, description, type) that are needed to create a new device for a give device type (which is defined by a client)
* Source client : Domogik admin, any other interface which can create some devices
* Target client : always 'admin'

@apiExample {python} Example usage:
    cli = MQSyncReq(zmq.Context())
    msg = MQMessage()
    msg.set_action('device.params')
    msg.add_data('device_type', 'diskfree.disk_usage')
    msg.add_data('client_id', 'plugin-diskfree.darkstar')
    print(cli.request('admin', msg.get(), timeout=10).get())

@apiParam {String} device_type The device type

@apiSuccessExample {json} Success-Response:
[
    'device.params.result',
    '{
        "result": {
            "xpl_stats": {

            },
            "name": "",
            "reference": "",
            "xpl": [
                {
                    "type": "string",
                    "description": "The path to look at.",
                    "key": "device"
                }
            ],
            "xpl_commands": {

            },
            "global": [
                {
                    "type": "integer",
                    "description": "The time in minutes between each check.",
                    "key": "interval"
                }
            ],
            "device_type": "diskfree.disk_usage",
            "description": ""
        }
    }'
]
"""

import zmq
from zmq.eventloop.ioloop import IOLoop
from domogikmq.reqrep.client import MQSyncReq
from domogikmq.message import MQMessage

cli = MQSyncReq(zmq.Context())
msg = MQMessage()
msg.set_action('device.params')
msg.add_data('device_type', 'velbus.dimmer')
msg.add_data('client_id', 'plugin-velbus.darkstar')
print(cli.request('admin', msg.get(), timeout=10).get())

