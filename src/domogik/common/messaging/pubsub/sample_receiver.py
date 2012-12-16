#!/usr/bin/python
# -*- coding: utf-8 -*-

# PUB-SUB receiver

import json
import sys
from messaging_event_utils import MessagingEventSub

def main(category_filter, action_filter):
    print("PUB-SUB receiver")
    sub_event = MessagingEventSub(category_filter, action_filter)

    while True:
        msg = json.loads(sub_event.wait_for_event())
        print("Id : %s - Content : %s" %(msg['id'], msg['content']))

if __name__ == "__main__":
    category_filter = None
    action_filter = None
    if len(sys.argv) > 1:
        category_filter = sys.argv[1]
    if len(sys.argv) > 2:
        action_filter = sys.argv[2]
    main(category_filter, action_filter)

