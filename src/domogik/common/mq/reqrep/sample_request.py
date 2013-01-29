#!/usr/bin/python
# -*- coding: utf-8 -*-

# Sample Request

from messaging_reqrep import MessagingReq
from random import choice

print("Requester sample")

categories = {
    'package' : ['list', 'install', 'uninstall'],
    'plugin' : ['list', 'enable', 'disable'],
}

msg_req = MessagingReq()
i=0
while True:
    category = choice(categories.keys())
    action = choice(categories[category])
    request = "request%s" % i
    reply = msg_req.send_request(category, action, request)
    print("Received reply %s" % reply)
    i += 1

