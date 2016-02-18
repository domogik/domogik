#!/usr/bin/python
"""
@api {REQ} device.update Create a Domogik device
@apiVersion 0.4.0
@apiName device.update
@apiGroup Devices
@apiDescription This request is used to ask Domogik's dbmgr to update a Domogik device in database. 
* Source client : Domogik admin, any other interface which can create some devices
* Target client : always 'dbmgr'

@apiExample {python} Example usage:
    cli = MQSyncReq(zmq.Context())
    msg = MQMessage()
    msg.set_action('device.update')
    msg.add_data('did', <id>)
    msg.add_data('name', <name>)
    msg.add_data('description', <description>)
    msg.add_data('reference', <reference>)
    print(cli.request('dbmgr', msg.get(), timeout=10).get())
        
    Here is a json example:
    {
        u'status': True,
        u'reason': None
    }
"""

import zmq
from zmq.eventloop.ioloop import IOLoop
from domogikmq.reqrep.client import MQSyncReq
from domogikmq.message import MQMessage

cli = MQSyncReq(zmq.Context())
msg = MQMessage()
msg.set_action('device.update')
msg.add_data('did', 1)
msg.add_data('name', "new name")
msg.add_data('description', "new description")
msg.add_data('reference', "new reference")
print(cli.request('dbmgr', msg.get(), timeout=10).get())

