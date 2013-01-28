#!/usr/bin/python
# -*- coding: utf-8 -*-

""" This file is part of B{Domogik} project (U{http://www.domogik.org}).

License
=======

B{Domogik} is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

B{Domogik} is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Domogik. If not, see U{http://www.gnu.org/licenses}.

Purpose
=======

Regression tests for the earth plugin.
Make tests for the MQ Pub subsystem

Usage
=====

Start plugin and run the tests
All publish updates are maid by the REQ tests, so you must now launh
./earthzmq_test.py in a second terminal.
Do a second run suing the xpl tests
./earth_test.py in a second terminal.

@author: bibi21000 <sgallet@gmail.com>
@copyright: (C) 2007-2013 Domogik project
@license: GPL(v3)
@organization: Domogik
"""
import datetime
from threading import Event
from domogik.xpl.common.xplconnector import Listener
from domogik.xpl.common.xplmessage import XplMessage
from domogik.xpl.common.plugin import XplPlugin
from domogik.common.messaging.reqrep.messaging_reqrep import MessagingReq
from domogik.common.messaging.pubsub.messaging_event_utils import MessagingEventSub
import unittest
import time
import json

#!/usr/bin/python
# -*- coding: utf-8 -*-

""" This file is part of B{Domogik} project (U{http://www.domogik.org}).

License
=======

B{Domogik} is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

B{Domogik} is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Domogik. If not, see U{http://www.gnu.org/licenses}.

Purpose
=======

Regression tests for the earth plugin.
Make tests for the MQ Req subsystem

Usage
=====

Start plugin and run the tests
You can also make the PUB test at the same time. Look at corresponding file.

@author: bibi21000 <sgallet@gmail.com>
@copyright: (C) 2007-2013 Domogik project
@license: GPL(v3)
@organization: Domogik
"""
import datetime
from threading import Event
from domogik.xpl.common.xplconnector import Listener
from domogik.xpl.common.xplmessage import XplMessage
from domogik.xpl.common.plugin import XplPlugin
from domogik.common.messaging.reqrep.messaging_reqrep import MessagingReq
from domogik.common.messaging.pubsub.messaging_event_utils import MessagingEventSub
import unittest
import time
import json
from time import sleep
from json import dumps, loads, JSONEncoder, JSONDecoder
import pickle

class PythonObjectEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (list, dict, str, unicode, int, float, bool, type(None))):
            return JSONEncoder.default(self, obj)
        return {'_python_object': pickle.dumps(obj)}

def as_python_object(dct):
    if '_python_object' in dct:
        return pickle.loads(str(dct['_python_object']))
    return dct

class PluginTestCase(unittest.TestCase):

    def setUp(self):
        #global messagingreq
        #self.messaging_req = messagingreq
        #global sendrequest
        #self.__sendrequest = sendrequest
        #self.messaging_req = MessagingReq()
        self.category = "plugin.earth"

    def tearDown(self):
        #self.messaging_req.s_req.close()
        self.messaging_sub.s_recv.close()

    def wait_pub(self, category_filters, action, dictkeys=[], dictkeyvals={}):
        '''
        Xait for a publish message from the plugin.

        :param key: a key to look for
        :type key: str
        :param testmsg: The message to send
        :param testmsg: XPLMessage
        :param dictkeys: The keys that must exist in the returning message
        :type dictkeys: set()
        :param dictkeyvals: The key:val pairs that must exist ine the returning message
        :param dictkeyvals: disct()

        '''
        self.messaging_sub = MessagingEventSub('plugin_earth', *category_filters)
        res = False
        self.time_start = datetime.datetime.now()
        duration = datetime.datetime.now() - self.time_start
        while (duration.seconds < 60) and (res!=True):
            duration = datetime.datetime.now() - self.time_start
            msg = self.messaging_sub.wait_for_event()
            #print(msg)
            request = json.loads(msg['content'], object_hook=as_python_object)
            content = request
            if (action == content['action']):
                #print(action)
                res = True
                if ('error' not in content['data']):
                    if (dictkeys != None) :
                        for mykey in dictkeys :
                            if (mykey not in content['data']) :
                                res = False
                    if (dictkeyvals != None) :
                        for mykey in dictkeyvals :
                            #print(mykey)
                            #print(dictkeyvals[mykey])
                            if (mykey not in content['data']) :
                                res = False
                                #print(mykey)
                            elif (content['data'][mykey] != dictkeyvals[mykey]) :
                                res = False
                                #print(dictkeyvals[mykey])
                    #print(res)
                    if (res == True) :
                        #print(res)
                        return True
        #print(res)
        return res

class GeneralTestCase(PluginTestCase):
    pass

class AdminTestCase(PluginTestCase):
    def test_010_list_node_added(self):
        keys = ['evnt-list','count']
        action = "event-added"
        keyvalss = None
        self.assertTrue(self.wait_pub([self.category + ".admin.list"], action, keys, keyvalss))

    def test_110_event_added(self):
        keys = ['uptime', 'fullruntime', 'runtime', 'runs', 'next']
        keyvalss = {'current' : 'started'}
        action = "added"
        self.assertTrue(self.wait_pub([self.category + ".admin.event"], action, keys, keyvalss))

    def test_210_event_stopped(self):
        keys = ['uptime', 'fullruntime', 'runtime', 'runs', 'next']
        keyvalss = {'current' : 'stopped'}
        action = "stopped"
        self.wait_pub([self.category + ".admin.event"], action, keys, keyvalss)
        self.assertTrue(self.wait_pub([self.category + ".admin.event"], action, keys, keyvalss))

    def test_310_event_resumed(self):
        keys = ['uptime', 'fullruntime', 'runtime', 'runs', 'next']
        keyvalss = {'current' : 'started'}
        action = "resumed"
        self.assertTrue(self.wait_pub([self.category + ".admin.event"], action, keys, keyvalss))

    def test_410_status(self):
        keys = ['status', 'type']
        keyvalss = None
        action = "status"
        self.assertTrue(self.wait_pub([self.category + ".admin.status"], action, keys, keyvalss))

    def test_510_event_removed(self):
        keys = ['uptime', 'fullruntime', 'runtime', 'runs', 'next']
        keyvalss = {'current' : 'halted'}
        action = "removed"
        self.assertTrue(self.wait_pub([self.category + ".admin.event"], action, keys, keyvalss))

    def test_610_list_node_removed(self):
        keys = ['evnt-list','count']
        action = "event-removed"
        keyvalss = None
        self.assertTrue(self.wait_pub([self.category + ".admin.list"], action, keys, keyvalss))


if __name__ == '__main__':

    #unittest.main()
    suite = unittest.TestLoader().loadTestsFromTestCase(GeneralTestCase)
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(AdminTestCase))
    unittest.TextTestRunner(verbosity=3).run(suite)


