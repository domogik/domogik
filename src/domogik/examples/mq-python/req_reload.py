#!/usr/bin/python
"""
@api {REQ} reload Reload the configuration for core components
@apiVersion 0.4.0
@apiName reload
@apiGroup Reload
@apiDescription This request is used to ask Domogik's xplgw to reload data from database in order to handle newly created devices (or updated and deleted informations)
* Source client : Domogik admin, any other interface which can create some devices
* Target client : always 'xplgw'

@apiExample {python} Example usage:
    cli = MQSyncReq(zmq.Context())
    msg = MQMessage()
    msg.set_action('reload')
    print(cli.request('xplgw', msg.get(), timeout=10).get())
    
@apiSuccessExample {json} Success-Response:
['reload.result', '{}']
"""

import zmq
from zmq.eventloop.ioloop import IOLoop
from domogikmq.reqrep.client import MQSyncReq
from domogikmq.message import MQMessage

cli = MQSyncReq(zmq.Context())
msg = MQMessage()
msg.set_action('reload')
print(cli.request('xplgw', msg.get(), timeout=10).get())


