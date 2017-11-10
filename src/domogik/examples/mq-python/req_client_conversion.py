#!/usr/bin/python
"""
@api {REQ} client.conversion.get Request to get all the clients conversion functions
@apiVersion 0.4.0
@apiName client.conversion.get
@apiGroup Client
@apiDescription This request is used to ask Domogik's manager the list of all the conversion functions provided by the plugins
* Source client : XplGw core component 
* Target client : always 'manager' 

@apiExample {python} Example usage:
    cli = MQSyncReq(zmq.Context())
    msg = MQMessage()
    msg.set_action('client.conversion.get')
    print(cli.request('manager', msg.get(), timeout=10).get())

@apiSuccessExample {json} Success-Response:
[
    'client.conversion.result',
    '{
        "core-scenario.darkstar": null,
        "core-admin.darkstar": null,
        "core-xplgw.darkstar": null,
        "core-rest.darkstar": null,
        "plugin-diskfree.darkstar": {
            
        },
        "plugin-teleinfo.darkstar": {
            
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
msg.set_action('client.conversion.get')
print(cli.request('manager', msg.get(), timeout=10).get())


