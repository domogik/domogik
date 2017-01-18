#!/usr/bin/python
"""
@api {REQ} config.delete Delete all elements of a client configuration
@apiVersion 0.4.0
@apiName config.delete
@apiGroup Clients configuration
@apiDescription This request is used to ask Domogik's admin to delete all the configuration related to a client
* Source client : Domogik admin, any other interface which can manage the clients
* Target client : always 'admin' 

@apiExample {python} Example usage:
    cli = MQSyncReq(zmq.Context())
    msg = MQMessage()
    msg.set_action('config.delete')
    msg.add_data('type', 'plugin')
    msg.add_data('host', 'darkstar')
    msg.add_data('name', 'diskfree')
    print(cli.request('admin', msg.get(), timeout=10).get())

@apiParam {String} type The client type
@apiParam {String} host The host on which is hosted the client
@apiParam {String} name The client name 

@apiSuccessExample {json} Success-Response:
[
    'config.result',
    '{
        "status": true,
        "reason": "",
        "type": "plugin",
        "host": "darkstar",
        "name": "diskfree"
    }'
]
"""

import zmq
from zmq.eventloop.ioloop import IOLoop
from domogikmq.reqrep.client import MQSyncReq
from domogikmq.message import MQMessage

cli = MQSyncReq(zmq.Context())
msg = MQMessage()
msg.set_action('config.delete')
msg.add_data('type', 'plugin')
msg.add_data('host', 'darkstar')
msg.add_data('name', 'diskfree')
print(cli.request('admin', msg.get(), timeout=10).get())

