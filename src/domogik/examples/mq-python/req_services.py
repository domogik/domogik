#!/usr/bin/python

import zmq
from zmq.eventloop.ioloop import IOLoop
from domogikmq.reqrep.client import MQSyncReq
from domogikmq.message import MQMessage

cli = MQSyncReq(zmq.Context())
print cli.rawrequest('mmi.service', 'xplgw', timeout=10)

cli = MQSyncReq(zmq.Context())
print cli.rawrequest('mmi.services', '', timeout=10)

