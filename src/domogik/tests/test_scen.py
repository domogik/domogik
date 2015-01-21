#!/usr/bin/python
# -*- coding: utf-8 -*-

import zmq
import json
from time import sleep

from domogikmq.message import MQMessage
from domogikmq.reqrep.client import MQSyncReq

z = zmq.Context()
m = MQMessage('test.list', {})
m2 = MQMessage('parameter.list', {})
m3 = MQMessage('scenario.list', {})
m4 = MQMessage('action.list', {})
c = MQSyncReq(z)

print "==== List of tests ===="
tests = c.request('scenario', m.get())
print tests
print "==== List of parameters ===="
print c.request('scenario', m2.get())
print "==== List of conditions ===="
print c.request('scenario', m3.get())
print "==== List actions ===="
print c.request('scenario', m4.get())
print "==== Get one test ===="
print tests._data['result']
print type(tests._data['result'])
#tests_data = json.loads(tests._data['result'])
tests_data = tests._data['result']
test_k = tests_data.keys()[0]
test_v = tests_data[tests_data.keys()[0]]

print "Test name : %s" % test_k
print "Test value : %s" % test_v

print "==== Create an instance of %s ====" % test_k
m4 = MQMessage('test.new', {'obj': test_k})
uid = c.request('scenario', m4.get())
print "Create an instance of %s" % test_k
m5 = MQMessage('action.new', {'obj': 'log.LogAction'})
uid5 = c.request('scenario', m5.get())
m6 = MQMessage('action.new', {'obj': 'log.LogAction'})
uid6 = c.request('scenario', m5.get())

print "Got UUID for test: %s" % uid._data['result']
print "Got UUID for action: %s" % uid5._data['result']
print "Got UUID for action: %s" % uid6._data['result']


print "==== Set needed parameters ===="
for a_value in test_v:
    print a_value
    k = a_value["name"]
    v = a_value["values"]
    print "    - %s" % k
    print "      > type : %s" % v["type"]
    print "      > expected tokens :"
    for tok in v["expected"]:
        vtok = v["expected"][tok]
        print "        * %s :" % tok
        print "          - default : %s" % vtok["default"]
        print "          - values : %s" % vtok["values"]
        print "          - type : %s" % vtok["type"]
        print "          - description : %s" % vtok["description"]
        print "          - filters : %s" % vtok["filters"]
print "  * Generating JSON with values :"
print "    - url.urlpath = http://localhost"
print "    - url.interval = 5"
print "    - text.text = Domogik"
src = """{
	"condition" : { 
		"NOT" : { 
			"%s" : {
        			"url": {
			            "urlpath": "http://localhost",
			            "interval" : "5"
			        },
        			"text": {
			            "text": "Domogik2"
        			}
    			}
		}
	},
   	"actions" : {
		"%s" : {
			"test": "ikke"
		}
	}
}""" % (uid._data['payload'], uid5._data['payload'])
print "  * JSON is : %s" % src
print "==== Create condition with this JSON"
m5 = MQMessage('scenario.new', {'name': 'foo', 'json_input': src})
cond = c.request('scenario', m5.get())
cond = cond._data['payload']['name']
print "Condition created with name : %s" % cond
m6 = MQMessage('scenario.get', {'name': cond})
parsed = c.request('scenario', m6.get())
print "Condition expression is : %s " % parsed
m7 = MQMessage('scenario.evaluate', {'name': cond})
print "Waiting for condition to be false (text exists in page)"
result = True
while result:
    parsed = c.request('scenario', m7.get())
    result = parsed._data['payload']['result']
    sleep(2)
print "Found text in url \o/"
m8 = MQMessage('action.list', {})
parsed = c.request('scenario', m8.get())
print "Got list of available actions : %s" % parsed._data['payload']
