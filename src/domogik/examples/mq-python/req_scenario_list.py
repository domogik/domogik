#!/usr/bin/python
"""
@apiIgnore TODO : This method is not yet documented
"""

import zmq
from zmq.eventloop.ioloop import IOLoop
from domogikmq.reqrep.client import MQSyncReq
from domogikmq.message import MQMessage

cli = MQSyncReq(zmq.Context())
msg = MQMessage()
msg.set_action('scenario.list')
print(cli.request('scenario', msg.get(), timeout=10).get())


