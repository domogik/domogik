#!/usr/bin/python
"""
@api {REQ} sensor.update Update a Domogik sensor
@apiVersion 0.4.0
@apiName sensor.create
@apiGroup Sensors
@apiDescription This request is used to ask Domogik's dbmgr to update a Domogik sensor in database. 
* Source client : Domogik admin, any other interface which can create some devices
* Target client : always 'dbmgr'

@apiExample {python} Example usage:
    cli = MQSyncReq(zmq.Context())
    msg = MQMessage()
    msg.set_action('sensor.update')
    msg.add_data('sid', <id>)
    msg.add_data('history_round', <round>)
    msg.add_data('history_store', <store>)
    msg.add_data('history_max', <max>)
    msg.add_data('history_expire', <expire>)
    msg.add_data('timeout', <timeout>)
    msg.add_data('formula', <formula>)
    print(cli.request('dbmgr', msg.get(), timeout=10).get())
        
    Here is a json example:
    {
        u'status': True,
        u'reason': None
    }
"""

import zmq
from zmq.eventloop.ioloop import IOLoop
from domogikmq.reqrep.client import MQSyncReq
from domogikmq.message import MQMessage

cli = MQSyncReq(zmq.Context())
msg = MQMessage()
msg.set_action('sensor.update')
msg.add_data('sid', 1)
msg.add_data('history_round', 0.5)
msg.add_data('history_store', 1)
msg.add_data('history_max', 1000)
msg.add_data('history_expire', 3600)
msg.add_data('timeout', 10)
msg.add_data('formula', "value - 1")
print(cli.request('dbmgr', msg.get(), timeout=10).get())

