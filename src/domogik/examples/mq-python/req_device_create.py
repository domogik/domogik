#!/usr/bin/python
"""
@api {REQ} device.create Create a Domogik device
@apiVersion 0.4.0
@apiName device.create
@apiGroup Devices
@apiDescription This request is used to ask Domogik's admin to create a new Domogik device in database. This is a quite complex command to use as you need before to get the list of parameters that can be set for a device, request the user to set these parameters and then create a json structure to send over the MQ.
* Source client : Domogik admin, any other interface which can create some devices
* Target client : always 'admin'

@apiExample {python} Example usage:
    cli = MQSyncReq(zmq.Context())
    msg = MQMessage()
    msg.set_action('device.create')
    msg.set_data({'data': {...}})
    print(cli.request('admin', msg.get(), timeout=10).get())
        
    Here is a json example:
    {
        u'xpl_stats': {
            
        },
        u'description': 'description',
        u'reference': 'reference',
        u'xpl': [
            
        ],
        u'xpl_commands': {
            
        },
        u'global': [
            {
                'value': '/dev/teleinfo',
                u'type': u'string',
                u'description': u'Theteleinformationmoduledevicepath(ex: /dev/teleinfoforanusbmodel).',
                u'key': u'device'
            },
            {
                'value': 60,
                u'type': u'integer',
                u'description': u'Thetimeinsecondsbetweeneachcheck.',
                u'key': u'interval'
            }
        ],
        u'client_id': u'plugin-teleinfo.darkstar',
        u'device_type': 'teleinfo.electric_meter',
        u'name': 'test_device_teleinfo'
    }

@apiParam {String} data The json data which represents the Domogik device to create. 


@apiSuccessExample {json} Success-Response:
[]
"""

import zmq
from zmq.eventloop.ioloop import IOLoop
from domogikmq.reqrep.client import MQSyncReq
from domogikmq.message import MQMessage

cli = MQSyncReq(zmq.Context())
msg = MQMessage()
msg.set_action('device.create')
msg.set_data({'data': {'some' : 'json content'}})
print(cli.request('admin', msg.get(), timeout=10).get())

