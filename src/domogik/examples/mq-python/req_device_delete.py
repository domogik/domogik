#!/usr/bin/python
"""
@api {REQ} device.update Create a Domogik device
@apiVersion 0.4.0
@apiName device.create
@apiGroup Devices
@apiDescription This request is used to ask Domogik's admin to delete a Domogik device in database. 
* Source client : Domogik admin, any other interface which can create some devices
* Target client : always 'admin'

@apiExample {python} Example usage:
    cli = MQSyncReq(zmq.Context())
    msg = MQMessage()
    msg.set_action('device.delete')
    msg.add_data('did', <id>)
    print(cli.request('admin', msg.get(), timeout=10).get())
        
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
msg.set_action('device.delete')
msg.add_data('did', 1)
print(cli.request('admin', msg.get(), timeout=10).get())

