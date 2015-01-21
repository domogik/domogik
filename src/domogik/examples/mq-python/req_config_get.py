#!/usr/bin/python
"""
@api {REQ} config.get Get a value for all configuration items of a client
@apiVersion 0.4.0
@apiName config.get for all elements
@apiGroup Clients configuration
@apiDescription This request is used to ask Domogik's dbmgr the value of a configuration item
* Source client : Domogik admin, any other interface which can manage the clients
* Target client : always 'dbmgr' 

@apiExample {python} Example usage:
    cli = MQSyncReq(zmq.Context())
    msg = MQMessage()
    msg.set_action('config.get')
    msg.add_data('type', 'plugin')
    msg.add_data('host', 'darkstar')
    msg.add_data('name', 'diskfree')
    msg.add_data('key', 'configured')
    print(cli.request('dbmgr', msg.get(), timeout=10).get())
    
@apiParam {String} type The client type
@apiParam {String} host The host on which is hosted the client
@apiParam {String} name The client name 
@apiParam {String} key The key of the configuration element

@apiSuccessExample {json} Success-Response:
[
    'config.result',
    '{
        "status": true,
        "name": "diskfree",
        "reason": "",
        "value": true,
        "host": "darkstar",
        "key": "configured",
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
msg.set_action('config.get')
msg.add_data('type', 'plugin')
msg.add_data('host', 'darkstar')
msg.add_data('name', 'diskfree')
msg.add_data('key', 'configured')
print(cli.request('dbmgr', msg.get(), timeout=10).get())

