#!/usr/bin/python
"""
@api {REQ} person.get Get the list of the persons
@apiVersion 0.6.0
@apiName person.get
@apiGroup Persons
@apiDescription This request is used to ask Domogik's admin the list of all the existing persons.
* Source client : Domoweb, Domogik admin, any other interface which can need to get the devices list
* Target client : always 'admin'

@apiExample {python} Example usage:
    cli = MQSyncReq(zmq.Context())
    msg = MQMessage()
    msg.set_action('person.get')
    print(cli.request('admin', msg.get(), timeout=10).get())

@apiSuccessExample {json} Success-Response:
[
    'device.result',
    '{
    }'
]
"""

import zmq
from zmq.eventloop.ioloop import IOLoop
from domogikmq.reqrep.client import MQSyncReq
from domogikmq.message import MQMessage

cli = MQSyncReq(zmq.Context())
msg = MQMessage()
msg.set_action('person.get')
print(cli.request('admin', msg.get(), timeout=10).get())

