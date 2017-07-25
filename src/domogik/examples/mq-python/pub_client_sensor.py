#!/usr/bin/python
# -*- coding: utf-8 -*-                                                                           
"""
@api {PUB} client.sensor Publish some client sansors values
@apiVersion 0.6.0
@apiName client.sensor
@apiGroup Client
@apiDescription Publish new sensor values
* Source client : Any plugin
* Target client : Domogik xplgw
This is a key/value pair, where the key is the sensorId and the value is the value to store.
Optional we can add an atTimestamp key, if this key is pressent we will use the value as the 
time to be stored in the db, otherwise the current timestamp will be used

@apiExample {python} Example usage:
        class Test():

            def __init__(self):
                pub = MQPub(zmq.Context(), 'example-pub')
                pub.send_event('client.sensor', \
                        {"12324" : 678, "3456" : 9999, "atTimestamp" : "1234567890"})

        if __name__ == "__main__":
            Test()
"""

import zmq
from domogikmq.pubsub.publisher import MQPub

class Test():

    def __init__(self):
        pub = MQPub(zmq.Context(), 'example-pub')
        pub.send_event('client.sensor', \
                {"12324" : 678, "3456" : 9999, "atTimestamp" : "1234567890"})

if __name__ == "__main__":
    Test()
