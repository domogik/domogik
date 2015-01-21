#!/usr/bin/python
"""
@apiIgnore TODO : is this dialog still needed ? Not sure!!!!
"""

import zmq
from zmq.eventloop.ioloop import IOLoop
from domogikmq.reqrep.client import MQSyncReq
from domogikmq.message import MQMessage

cli = MQSyncReq(zmq.Context())
msg = MQMessage()
msg.set_action('package.detail.get')
print(cli.request('manager', msg.get(), timeout=10).get())


