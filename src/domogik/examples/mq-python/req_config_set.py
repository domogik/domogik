#!/usr/bin/python

import zmq
from zmq.eventloop.ioloop import IOLoop
from domogik.mq.reqrep.client import MQSyncReq
from domogik.mq.message import MQMessage

cli = MQSyncReq(zmq.Context())
msg = MQMessage()
msg.set_action('config.set')
msg.add_data('type', 'plugin')
msg.add_data('host', 'darkstar')
msg.add_data('id', 'diskfree')
msg.add_data('data', {'interval' : 5, 'dummy' : 'foo'})
print cli.request('dbmgr', msg.get(), timeout=10).get()

