#!/usr/bin/python
# -*- coding: utf-8 -*-

# PUB-SUB receiver

import json
import sys
from messaging_event_utils import MessagingEventSub

def main(category_filter):
    print("PUB-SUB receiver")
    sub_event = MessagingEventSub('sample_receiver', category_filter)

    while True:
        msg = sub_event.wait_for_event()
        print(msg)

if __name__ == "__main__":
    category_filter = None
    if len(sys.argv) > 1:
        category_filter = sys.argv[1]
    main(category_filter)

