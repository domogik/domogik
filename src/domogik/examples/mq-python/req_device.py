#!/usr/bin/python
"""
@api {REQ} device.get Get the list of the created Domogik devices for a given client
@apiVersion 0.4.0
@apiName device.get
@apiGroup Devices
@apiDescription This request is used to ask Domogik's admin the list of all the existing Domogik devices for a client.
* Source client : Domogik admin, any other interface which can need to get the devices list
* Target client : always 'admin'

@apiExample {python} Example usage:
    # to get all devices of one client :
    cli = MQSyncReq(zmq.Context())
    msg = MQMessage()
    msg.set_action('device.get')
    msg.add_data('type', 'plugin')
    msg.add_data('name', 'diskfree')
    msg.add_data('host', 'darkstar')
    print(cli.request('admin', msg.get(), timeout=10).get())

    # to get all devices of all clients :
    cli = MQSyncReq(zmq.Context())
    msg = MQMessage()
    msg.set_action('device.get')
    print(cli.request('admin', msg.get(), timeout=10).get())

@apiParam {String} [type] The client type
@apiParam {String} [name] The client name 
@apiParam {String} [host] The host on which is hosted the client
    
@apiSuccessExample {json} Success-Response:
[
    'device.result',
    '{
        "status": true,
        "name": "diskfree",
        "reason": "",
        "devices": [
            {
                "xpl_stats": {
                    "get_total_space": {
                        "json_id": "get_total_space",
                        "name": "Total space",
                        "id": 29,
                        "parameters": {
                            "static": [
                                {
                                    "type": "string",
                                    "key": "device",
                                    "value": "/home"
                                },
                                {
                                    "type": null,
                                    "key": "type",
                                    "value": "total_space"
                                }
                            ],
                            "dynamic": [
                                {
                                    "ignore_values": "",
                                    "sensor_name": "get_total_space",
                                    "key": "current"
                                }
                            ]
                        },
                        "schema": "sensor.basic"
                    },
                    ...
                },
                "commands": {
                    
                },
                "description": "description",
                "reference": "reference",
                "xpl_commands": {
                    
                },
                "client_id": "plugin-diskfree.darkstar",
                "device_type_id": "diskfree.disk_usage",
                "sensors": {
                    "get_total_space": {
                        "conversion": "",
                        "value_min": null,
                        "data_type": "DT_Byte",
                        "reference": "get_total_space",
                        "last_received": 1412282409,
                        "value_max": 19684000000.0,
                        "incremental": false,
                        "timeout": 0,
                        "formula": null,
                        "last_value": "19683999744",
                        "id": 29,
                        "name": "Total Space"
                    },
                    ...
                },
                "parameters": {
                    "interval": {
                        "key": "interval",
                        "type": "integer",
                        "id": 8,
                        "value": "1"
                    }
                },
                "id": 8,
                "name": "test_device_diskfree"
            }
        ],
        "host": "darkstar",
        "type": "plugin"
    }'
]
"""

import zmq
from zmq.eventloop.ioloop import IOLoop
from domogikmq.reqrep.client import MQSyncReq
from domogikmq.message import MQMessage

cli = MQSyncReq(zmq.Context())
msg = MQMessage()
msg.set_action('device.get')
#msg.add_data('type', 'plugin')
#msg.add_data('name', 'diskfree')
#msg.add_data('host', 'darkstar')
print(cli.request('admin', msg.get(), timeout=10).get())

