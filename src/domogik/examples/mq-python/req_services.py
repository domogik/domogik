#!/usr/bin/python

import zmq
from zmq.eventloop.ioloop import IOLoop
from domogik.mq.reqrep.client import MQSyncReq
from domogik.mq.message import MQMessage

cli = MQSyncReq(zmq.Context())
print cli.rawrequest('mmi.service', 'xplgw', timeout=10)

cli = MQSyncReq(zmq.Context())
print cli.rawrequest('mmi.services', '', timeout=10)

