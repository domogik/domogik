#!/usr/bin/python

import zmq
from zmq.eventloop.ioloop import IOLoop
from domogik.mq.reqrep.client import MQSyncReq
from domogik.mq.message import MQMessage

cli = MQSyncReq(zmq.Context())
msg = MQMessage()
msg.set_action('plugin.stop.do')
msg.add_data('name', 'diskfree')
msg.add_data('host', 'darkstar')
print cli.request('diskfree', msg.get(), timeout=10).get()


