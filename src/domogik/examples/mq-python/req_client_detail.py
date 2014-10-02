#!/usr/bin/python
"""
@api {REQ} client.detail.get Request to get all the clients details
@apiVersion 0.4.0
@apiName client.detail.get
@apiGroup Client
@apiDescription This request is used to ask Domogik's manager the details for the available clients (core components, plugins, ...)
* Source client : Domogik admin, any other interface which can manage the plugins
* Target client : always 'manager' 

@apiExample {python} Example usage:
    cli = MQSyncReq(zmq.Context())
    msg = MQMessage()
    msg.set_action('client.detail.get')
    print(cli.request('manager', msg.get(), timeout=10).get())

@apiSuccessExample {json} Success-Response:
[
    'client.detail.result',
    '{
        "core-scenario.darkstar": {
            "status": "alive",
            "name": "scenario",
            "xpl_source": "domogik-scenario.darkstar",
            "data": {
                
            },
            "configured": null,
            "pid": 16037,
            "package_id": "core-scenario",
            "host": "darkstar",
            "type": "core",
            "last_seen": 1412278855.706537
        },
        "core-dbmgr.darkstar": {
            "status": "alive",
            "name": "dbmgr",
            "xpl_source": "domogik-dbmgr.darkstar",
            "data": {
                
            },
            "configured": null,
            "pid": 15935,
            "package_id": "core-dbmgr",
            "host": "darkstar",
            "type": "core",
            "last_seen": 1412278852.989411
        },
        "core-xplgw.darkstar": {
            "status": "alive",
            "name": "xplgw",
            "xpl_source": "domogik-xplgw.darkstar",
            "data": {
                
            },
            "configured": null,
            "pid": 16003,
            "package_id": "core-xplgw",
            "host": "darkstar",
            "type": "core",
            "last_seen": 1412278855.010364
        },
        "core-rest.darkstar": {
            "status": "alive",
            "name": "rest",
            "xpl_source": "domogik-rest.darkstar",
            "data": {
                
            },
            "configured": null,
            "pid": 15971,
            "package_id": "core-rest",
            "host": "darkstar",
            "type": "core",
            "last_seen": 1412278854.14476
        },
        "plugin-diskfree.darkstar": {
            "status": "unknown",
            "name": "diskfree",
            "xpl_source": "domogik-diskfree.darkstar",
            "data": {
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
                "udev_rules": {
                    
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
            },
            "configured": true,
            "pid": 16117,
            "package_id": "plugin-diskfree",
            "host": "darkstar",
            "type": "plugin",
            "last_seen": 1412278856.468071
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
msg.set_action('client.detail.get')
print(cli.request('manager', msg.get(), timeout=10).get())


