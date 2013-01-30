#!/usr/bin/python
# -*- coding: utf-8 -*-

# PUB-SUB emitter

import json
from mq_event_utils import MqEventPub
from random import choice
from time import sleep

print("PUB-SUB emitter sample")

categories = {
    'package' : {
                    'event' : ['installed', 'uninstalled'], 
                    'content': ['package1', 'package2']
    },
    'plugin' : {
                    'event' : ['enabled', 'disabled'],
                    'content' : ['teleinfo', 'zwave', 'x10', 'plcbus']
    },
    'device' : {
                    'event' : ['send_value'],
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
                    'event' : ['insert'],
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

pub_event = MqEventPub('sample_emitter')

while True:
    category1 = choice(categories.keys()) 
    category2 = choice(categories[category1]['event'])
    category = "%s.%s" % (category1, category2)
    j_content = json.dumps(choice(categories[category1]['content']))
    pub_event.send_event(category, j_content)
    print("Message sent : %s - %s"  % (category, j_content))
    sleep(2)

