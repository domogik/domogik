#!/usr/bin/python
# -*- coding: utf-8 -*-

# PUB-SUB receiver

import json
import sys
from mq_event_utils import MqAsyncSub
from zmq.eventloop.ioloop import IOLoop

def main():
    print("PUB-SUB receiver")
    category_filters = []
    category_filters.append( "device" )
    category_filters.append( "package" )
    sub_event = MqAsyncSub('sample_receiver', category_filters)
    IOLoop.instance().start()

def _plugin(self, msg):
    print "plugin"
    print msg

if __name__ == "__main__":
    main()

