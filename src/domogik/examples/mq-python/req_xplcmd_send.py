#!/usr/bin/python

import zmq
from zmq.eventloop.ioloop import IOLoop
from domogikmq.reqrep.client import MQSyncReq
from domogikmq.message import MQMessage

cli = MQSyncReq(zmq.Context())
msg = MQMessage()
msg.set_action('cmd.send')
msg.add_data('cmdid', 1)
msg.add_data('cmdparams', {'level': 0})
print cli.request('xplgw', msg.get(), timeout=10).get()


