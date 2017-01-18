#!/usr/bin/python
"""
@api {REQ} client.list.get Request to get all the clients list
@apiVersion 0.4.0
@apiName client.list.get
@apiGroup Client
@apiDescription This request is used to ask Domogik's manager the list of the available clients (core components, plugins, ...)
* Source client : Domogik admin, any other interface which can manage the plugins
* Target client : always 'manager' 

@apiExample {python} Example usage:
    cli = MQSyncReq(zmq.Context())
    msg = MQMessage()
    msg.set_action('client.list.get')
    print(cli.request('manager', msg.get(), timeout=10).get())

@apiSuccessExample {json} Success-Response:
[
    'client.list.result',
    '{
        "core-scenario.darkstar": {
            "status": "alive",
            "name": "scenario",
            "xpl_source": "domogik-scenario.darkstar",
            "configured": null,
            "pid": 16037,
            "package_id": "core-scenario",
            "host": "darkstar",
            "type": "core",
            "last_seen": 1412278856.409031
        },
        "core-admin.darkstar": {
            "status": "alive",
            "name": "admin",
            "xpl_source": "domogik-admin.darkstar",
            "configured": null,
            "pid": 15935,
            "package_id": "core-admin",
            "host": "darkstar",
            "type": "core",
            "last_seen": 1412278854.144102
        },
        "core-xplgw.darkstar": {
            "status": "alive",
            "name": "xplgw",
            "xpl_source": "domogik-xplgw.darkstar",
            "configured": null,
            "pid": 16003,
            "package_id": "core-xplgw",
            "host": "darkstar",
            "type": "core",
            "last_seen": 1412278855.705864
        },
        "core-rest.darkstar": {
            "status": "alive",
            "name": "rest",
            "xpl_source": "domogik-rest.darkstar",
            "configured": null,
            "pid": 15971,
            "package_id": "core-rest",
            "host": "darkstar",
            "type": "core",
            "last_seen": 1412278855.009676
        },
        "plugin-diskfree.darkstar": {
            "status": "unknown",
            "name": "diskfree",
            "xpl_source": "domogik-diskfree.darkstar",
            "configured": true,
            "pid": 16117,
            "package_id": "plugin-diskfree",
            "host": "darkstar",
            "type": "plugin",
            "last_seen": 1412278856.468068
        },
        "plugin-teleinfo.darkstar": {
            "status": "unknown",
            "name": "teleinfo",
            "xpl_source": "domogik-teleinfo.darkstar",
            "configured": false,
            "pid": 0,
            "package_id": "plugin-teleinfo",
            "host": "darkstar",
            "type": "plugin",
            "last_seen": 1412278856.43876
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
msg.set_action('client.list.get')
print(cli.request('manager', msg.get(), timeout=10).get())


