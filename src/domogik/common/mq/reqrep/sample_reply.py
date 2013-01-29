#!/usr/bin/python
# -*- coding: utf-8 -*-

# Sample Reply

import json
from mq_reqrep_utils import MqRep
from time import sleep

print("Reply sample")

msg_rep = MqRep()

while True:
    print("Waiting for request...")
    j_request = msg_rep.wait_for_request()
    print("Received request %s" % j_request)
    print("Processing request...")
    request = json.loads(j_request)
    sleep(2)
    msg_rep.send_reply("%s : done!" % request['id'])
