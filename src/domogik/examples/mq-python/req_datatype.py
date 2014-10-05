#!/usr/bin/python
"""
@api {REQ} datatype.get Get the list of all defined datatypes
@apiVersion 0.4.0
@apiName datatype.get 
@apiGroup Datatypes
@apiDescription This request is used to ask Domogik's manager the list of all defined datatypes
* Source client : Any client that need the datatypes list (user interfaces for example)
* Target client : always 'manager' 

@apiExample {python} Example usage:
    cli = MQSyncReq(zmq.Context())
    msg = MQMessage()
    msg.set_action('datatype.get')
    print(cli.request('manager', msg.get(), timeout=10).get())
    
@apiSuccessExample {json} Success-Response:
[
    'datatype.result',
    '{
        "datatypes": {
            "DT_HVACVent": {
                "childs": [
                    
                ],
                "values": {
                    "1": "Heat",
                    "0": "Auto",
                    "3": "Fan only",
                    "2": "Cool",
                    "4": "Dry"
                }
            },
            "DT_OpenClose": {
                "labels": {
                    "1": "Close",
                    "0": "Open"
                },
                "childs": [
                    
                ],
                "parent": "DT_Bool"
            },
            ...
        }
    }'
]
"""

import zmq
from zmq.eventloop.ioloop import IOLoop
from domogikmq.reqrep.client import MQSyncReq
from domogikmq.message import MQMessage

cli = MQSyncReq(zmq.Context())
msg = MQMessage()
msg.set_action('datatype.get')
print(cli.request('manager', msg.get(), timeout=10).get())

