#!/usr/bin/python

import zmq
from zmq.eventloop.ioloop import IOLoop
from domogikmq.reqrep.client import MQSyncReq
from domogikmq.message import MQMessage

cli = MQSyncReq(zmq.Context())
msg = MQMessage()
msg.set_action('helper.do')
msg.add_data('command', 'scan')
msg.add_data('params', {'test1': 'foo', 'test2': 'bar'} )
print cli.request('velbus', msg.get(), timeout=10).get()

