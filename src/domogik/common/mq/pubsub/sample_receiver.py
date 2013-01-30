#!/usr/bin/python
# -*- coding: utf-8 -*-

# PUB-SUB receiver

import json
import sys
from mq_event_utils import MqEventSub

def main(*category_filters):
    print("PUB-SUB receiver")
    sub_event = MqEventSub('sample_receiver', *category_filters)

    while True:
        msg = sub_event.wait_for_event()
        print(msg)

if __name__ == "__main__":
    category_filters = []
    if len(sys.argv) > 1:
        # args are filters
        category_filters = sys.argv[1:]
    main(*category_filters)

