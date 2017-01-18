#!/usr/bin/python
"""
@api {REQ} sensor_history.get Get the last values of a sensor history 
@apiVersion 0.5.0
@apiName sensor_history.get
@apiGroup Sensors
@apiDescription This request is used to ask Domogik's admin the last values of the history of a sensor.
* Source client : Domogik admin, any other interface which can need to get the sensor last value
* Target client : always 'admin'

@apiExample {python} Example usage:
    cli = MQSyncReq(zmq.Context())

    # example 1 : get the latest value
    msg = MQMessage()
    msg.set_action('sensor_history.get')
    msg.add_data('sensor_id', 3)
    msg.add_data('mode', 'last')
    msg.add_data('number', 1)
    print(cli.request('admin', msg.get(), timeout=10).get())
    
    # example 2 : get the last N values
    msg = MQMessage()
    msg.set_action('sensor_history.get')
    msg.add_data('sensor_id', 3)
    msg.add_data('mode', 'last')
    msg.add_data('number', 3)
    print(cli.request('admin', msg.get(), timeout=10).get())
    
    # example 3 : get the values since a timestamp
    msg = MQMessage()
    msg.set_action('sensor_history.get')
    msg.add_data('sensor_id', 3)
    msg.add_data('mode', 'period')
    msg.add_data('from', 1449178465)
    print(cli.request('admin', msg.get(), timeout=10).get())

@apiParam {String} sensor_id The sensor id
@apiParam {String} mode The mode : 'last' to get the last values, 'period' to get the values rom a period.
@apiParam {String} [number] If mode = 'last', set the number of values to get.
@apiParam {String} [from] If mode = 'period', set the timestamp from which you want to get the values
@apiParam {String} [to] If mode = 'period', set the timestamp to which you want to get the values. If this parameter is not set, the 'to' value is the current time.
    
@apiSuccessExample {json} Success-Response:
    ['sensor_history.result', '{"status": true, "reason": "", "sensor_id": 3, "values": [{"timestamp": 1449216514.0, "value_str": "0688459268", "value_num": 688459000.0}, {"timestamp": 1449181378.0, "value_str": "0688459268", "value_num": 688459000.0}, {"timestamp": 1449178485.0, "value_str": "0102030405", "value_num": 102030000.0}]}']
"""

"""
@api {REQ} sensor_history.get Get the last value of a sensor history 
@apiVersion 0.4.0
@apiName sensor_history.get
@apiGroup Sensors
@apiDescription This request is used to ask Domogik's admin the last value of the history of a sensor.
* Source client : Domogik admin, any other interface which can need to get the sensor last value
* Target client : always 'admin'

@apiExample {python} Example usage:
    cli = MQSyncReq(zmq.Context())
    msg = MQMessage()
    msg.set_action('sensor_history.get')
    msg.add_data('sensor_id', 190)
    print(cli.request('admin', msg.get(), timeout=10).get())
    


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

# example 1 : get the latest value
msg = MQMessage()
msg.set_action('sensor_history.get')
msg.add_data('sensor_id', 3)
msg.add_data('mode', 'last')
msg.add_data('number', 1)
print(cli.request('admin', msg.get(), timeout=10).get())

# example 2 : get the last N values
msg = MQMessage()
msg.set_action('sensor_history.get')
msg.add_data('sensor_id', 3)
msg.add_data('mode', 'last')
msg.add_data('number', 3)
print(cli.request('admin', msg.get(), timeout=10).get())

# example 3 : get the values since a timestamp
msg = MQMessage()
msg.set_action('sensor_history.get')
msg.add_data('sensor_id', 3)
msg.add_data('mode', 'period')
msg.add_data('from', 1449178465)
print(cli.request('admin', msg.get(), timeout=10).get())

