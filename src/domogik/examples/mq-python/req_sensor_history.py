#!/usr/bin/python
"""
@api {REQ} sensor_history.get Get the last value of a sensor history 
@apiVersion 0.4.0
@apiName sensor_history.get
@apiGroup Sensors
@apiDescription This request is used to ask Domogik's dbmgr the last value of the history of a sensor.
* Source client : Domogik admin, any other interface which can need to get the sensor last value
* Target client : always 'dbmgr'

@apiExample {python} Example usage:
    cli = MQSyncReq(zmq.Context())
    msg = MQMessage()
    msg.set_action('sensor_history.get')
    msg.add_data('sensor_id', 190)
    print(cli.request('dbmgr', msg.get(), timeout=10).get())

@apiParam {String} sensor_id The sensor id
    
@apiSuccessExample {json} Success-Response:
[
    'sensor_history.result',
    '{
        "status": true,
        "reason": "",
        "sensor_id": 190,
        "values": [
            "1027.3"
        ]
    }'
]
"""

import zmq
from zmq.eventloop.ioloop import IOLoop
from domogikmq.reqrep.client import MQSyncReq
from domogikmq.message import MQMessage

cli = MQSyncReq(zmq.Context())
msg = MQMessage()
msg.set_action('sensor_history.get')
msg.add_data('sensor_id', 189)
print(cli.request('dbmgr', msg.get(), timeout=10).get())

