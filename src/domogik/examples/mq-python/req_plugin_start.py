#!/usr/bin/python

import zmq
from zmq.eventloop.ioloop import IOLoop
from domogikmq.reqrep.client import MQSyncReq
from domogikmq.message import MQMessage

cli = MQSyncReq(zmq.Context())
msg = MQMessage()
msg.set_action('plugin.start.do')
msg.add_data('name', 'diskfree')
msg.add_data('host', 'darkstar')
print cli.request('manager', msg.get(), timeout=10).get()


