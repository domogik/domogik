#!/usr/bin/python

import zmq
from zmq.eventloop.ioloop import IOLoop
from domogikmq.reqrep.client import MQSyncReq
from domogikmq.message import MQMessage

cli = MQSyncReq(zmq.Context())
msg = MQMessage()
msg.set_action('plugin.stop.do')
msg.add_data('name', 'diskfree')
msg.add_data('host', 'darkstar')
print cli.request('plugin-diskfree.darkstar', msg.get(), timeout=10).get()


