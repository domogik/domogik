#!/usr/bin/python

import zmq
from zmq.eventloop.ioloop import IOLoop
from domogik.mq.reqrep.client import MQSyncReq
from domogik.mq.message import MQMessage

cli = MQSyncReq(zmq.Context())
msg = MQMessage()
msg.set_action('device.params')
msg.set_data({'device_type': 'velbus.relay'})
print cli.request('dbmgr', msg.get(), timeout=10).get()

