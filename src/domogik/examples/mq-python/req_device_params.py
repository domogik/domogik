#!/usr/bin/python

import zmq
from zmq.eventloop.ioloop import IOLoop
from domogikmq.reqrep.client import MQSyncReq
from domogikmq.message import MQMessage

cli = MQSyncReq(zmq.Context())
msg = MQMessage()
msg.set_action('device.params')
msg.set_data({'device_type': 'knxplugin.switch'})
print cli.request('dbmgr', msg.get(), timeout=10).get()

