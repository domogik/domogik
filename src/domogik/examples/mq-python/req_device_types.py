#!/usr/bin/python
"""
@api {REQ} device_types.get Get the available device_types for a Domogik client.
@apiVersion 0.4.0
@apiName device_types.get
@apiGroup Devices
@apiDescription This request is used to ask Domogik's manager the list of the device types for a client.
* Source client : Domogik admin, any other interface which can create some devices
* Target client : always 'manager'

@apiExample {python} Example usage:
    cli = MQSyncReq(zmq.Context())
    msg = MQMessage()
    msg.set_action('device_types.get')
    msg.add_data('device_type', 'diskfree.disk_usage')
    print(cli.request('manager', msg.get(), timeout=10).get())
    
@apiParam {String} [device_type] The device type. If given, return only the requested device type. Else return all the existing device types

@apiSuccessExample {json} Success-Response:
[
    'device_types.result',
    '{
        "diskfree.disk_usage": {
            "xpl_stats": {
                "get_total_space": {
                    "name": "Total space",
                    "parameters": {
                        "device": [
                            
                        ],
                        "static": [
                            {
                                "key": "type",
                                "value": "total_space"
                            }
                        ],
                        "dynamic": [
                            {
                                "ignore_values": "",
                                "sensor": "get_total_space",
                                "key": "current"
                            }
                        ]
                    },
                    "schema": "sensor.basic"
                },
                "get_free_space": {
                    "name": "Free space",
                    "parameters": {
                        "device": [
                            
                        ],
                        "static": [
                            {
                                "key": "type",
                                "value": "free_space"
                            }
                        ],
                        "dynamic": [
                            {
                                "ignore_values": "",
                                "sensor": "get_free_space",
                                "key": "current"
                            }
                        ]
                    },
                    "schema": "sensor.basic"
                },
                "get_used_space": {
                    "name": "Used space",
                    "parameters": {
                        "device": [
                            
                        ],
                        "static": [
                            {
                                "key": "type",
                                "value": "used_space"
                            }
                        ],
                        "dynamic": [
                            {
                                "ignore_values": "",
                                "sensor": "get_used_space",
                                "key": "current"
                            }
                        ]
                    },
                    "schema": "sensor.basic"
                },
                "get_percent_used": {
                    "name": "Percent used",
                    "parameters": {
                        "device": [
                            
                        ],
                        "static": [
                            {
                                "key": "type",
                                "value": "percent_used"
                            }
                        ],
                        "dynamic": [
                            {
                                "ignore_values": "",
                                "sensor": "get_percent_used",
                                "key": "current"
                            }
                        ]
                    },
                    "schema": "sensor.basic"
                }
            },
            "commands": {
                
            },
            "device_types": {
                "diskfree.disk_usage": {
                    "commands": [
                        
                    ],
                    "name": "Disk usage",
                    "parameters": [
                        {
                            "type": "string",
                            "description": "The path to look at.",
                            "key": "device",
                            "xpl": true
                        },
                        {
                            "type": "integer",
                            "description": "The time in minutes between each check.",
                            "key": "interval",
                            "xpl": false
                        }
                    ],
                    "sensors": [
                        "get_total_space",
                        "get_percent_used",
                        "get_free_space",
                        "get_used_space"
                    ],
                    "id": "diskfree.disk_usage",
                    "description": "Disk usage"
                }
            },
            "xpl_commands": {
                
            },
            "products": [
                
            ],
            "sensors": {
                "get_total_space": {
                    "conversion": "",
                    "name": "Total Space",
                    "data_type": "DT_Byte",
                    "incremental": false,
                    "timeout": 0,
                    "history": {
                        "max": 0,
                        "duplicate": false,
                        "expire": 0,
                        "round_value": 0,
                        "store": true
                    }
                },
                "get_free_space": {
                    "conversion": "",
                    "name": "Free Space",
                    "data_type": "DT_Byte",
                    "incremental": false,
                    "timeout": 0,
                    "history": {
                        "max": 0,
                        "duplicate": false,
                        "expire": 0,
                        "round_value": 0,
                        "store": true
                    }
                },
                "get_used_space": {
                    "conversion": "",
                    "name": "Used Space",
                    "data_type": "DT_Byte",
                    "incremental": false,
                    "timeout": 0,
                    "history": {
                        "max": 0,
                        "duplicate": false,
                        "expire": 0,
                        "round_value": 0,
                        "store": true
                    }
                },
                "get_percent_used": {
                    "conversion": "",
                    "name": "Percent used",
                    "data_type": "DT_Scaling",
                    "incremental": false,
                    "timeout": 0,
                    "history": {
                        "max": 0,
                        "duplicate": false,
                        "expire": 0,
                        "round_value": 0,
                        "store": true
                    }
                }
            },
            "configuration": [
                {
                    "description": "Automatically start the plugin at Domogik startup",
                    "default": false,
                    "required": true,
                    "key": "auto_startup",
                    "type": "boolean",
                    "name": "Start the plugin with Domogik"
                }
            ],
            "identity": {
                "description": "Send over xPL disk usage",
                "author": "Fritz",
                "author_email": "fritz.smh at gmail.com",
                "tags": [
                    "computer"
                ],
                "icon_file": "/var/lib/domogik//domogik_packages/plugin_diskfree/design/icon.png",
                "domogik_min_version": "0.4.0",
                "package_id": "plugin-diskfree",
                "dependencies": [
                    
                ],
                "version": "1.0",
                "type": "plugin",
                "name": "diskfree"
            },
            "json_version": 2
        }
    }'
]"""

import zmq
from zmq.eventloop.ioloop import IOLoop
from domogikmq.reqrep.client import MQSyncReq
from domogikmq.message import MQMessage

cli = MQSyncReq(zmq.Context())
msg = MQMessage()
msg.set_action('device_types.get')
#msg.add_data('device_type', 'diskfree.disk_usage')
print(cli.request('manager', msg.get(), timeout=10).get())


