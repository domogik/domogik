#!/usr/bin/python
# -*- coding: utf-8 -*-

# PUB-SUB emitter

import json
from messaging_event import MessagingEventPub
from random import choice
from time import sleep

print("PUB-SUB emitter sample")

categories = {
    'package' : ['installed', 'uninstalled'],
    'plugin' : ['enabled', 'disabled'],
}

content = ["Domogik is really cool", "I like Domoweb", "Domogik is magic"]

pub_event = MessagingEventPub()

while True:
    category = choice(categories.keys())
    action = choice(categories[category])
    j_content = json.dumps({"content" : "%s" % choice(content)})
    pub_event.send_message(category, action, j_content)

