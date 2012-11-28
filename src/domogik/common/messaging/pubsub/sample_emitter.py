#!/usr/bin/python
# -*- coding: utf-8 -*-

# PUB-SUB emitter

import json
from messaging_event import MessagingEventPub
from random import choice
from time import sleep

print("PUB-SUB emitter sample")

categories = {
    'package' : {
                    'action' : ['installed', 'uninstalled'], 
                    'content': ['package1', 'package2']
    },
    'plugin' : {
                    'action' : ['enabled', 'disabled'],
                    'content' : ['teleinfo', 'zwave', 'x10', 'plcbus']
    },
    'device' : {
                    'action' : ['send_value'],
                    'content' : [
                                    {
                                        'source': 'rfxcom', 
                                        'device_id': 3, 
                                        'data': [
                                            {'value': '13', 'key': 'temperature'}
                                        ]
                                    }
                    ]
    },
    'database' : {
                    'action' : ['insert'],
                    'content' : [
                                    {
                                        'source': 'core_device', 
                                        'data': [
                                            {'id': '14', 'name': 'My device'}
                                        ]
                                    }
                    ]
    },    
}

content = ["Domogik is really cool", "I like Domoweb", "Domogik is magic"]

pub_event = MessagingEventPub()

while True:
    category = choice(categories.keys())
    action = choice(categories[category]['action'])
    j_content = json.dumps({"content" : "%s" % choice(categories[category]['content'])})
    pub_event.send_event(category, action, j_content)
    sleep(2)

