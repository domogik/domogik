#!/usr/bin/python

import zmq
from zmq.eventloop.ioloop import IOLoop
from domogikmq.reqrep.client import MQSyncReq
from domogikmq.message import MQMessage

cli = MQSyncReq(zmq.Context())
msg = MQMessage()
msg.set_action('device.get')
msg.add_data('type', 'plugin')
msg.add_data('name', 'diskfree')
msg.add_data('host', 'darkstar')
print cli.request('dbmgr', msg.get(), timeout=10).get()

