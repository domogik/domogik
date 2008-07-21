#!/usr/bin/python
# -*- encoding:utf-8 -*-

# $LastChangedBy: mschneider $
# $LastChangedDate: 2008-07-21 09:38:29 +0200 (lun. 21 juil. 2008) $
# $LastChangedRevision: 91 $

from xPLAPI import *
from onewire import *

myow = OneWire()
myow.set_cache_use(False)
myxpl = Manager(ip = "192.168.1.22",port = 5034)
my_temp_message = Message()
my_temp_message.set_type("xpl-trig")
my_temp_message.set_schema("sensor.basic")
my_x10_mess = Message()
my_x10_mess.set_type("xpl-cmnd")
my_x10_mess.set_schema("x10.basic")

def test():
    for  (i, t, v) in myow.get_temperature():
        print "ITEM : "+ i +" - " + v
        my_temp_message.set_data_key("device", i)
        my_temp_message.set_data_key("type", t)
        my_temp_message.set_data_key("current", v) 
        myxpl.send(my_temp_message)
        if float(v) > 23.0:
            my_x10_mess.set_data_key("device","A3")
            my_x10_mess.set_data_key("command","on")
            myxpl.send( my_x10_mess )


t = xPLTimer(15, test)
t.start()

