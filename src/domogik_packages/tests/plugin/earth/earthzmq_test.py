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

Usage
=====

Start plugin and run the tests

@author: bibi21000 <sgallet@gmail.com>
@copyright: (C) 2007-2012 Domogik project
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

class PluginTestCase(unittest.TestCase):

    def send_request(self, category, action, request, dictkeys=[], dictkeyvals={}):
        '''
        Send a request to the ZMQ and wait for reply

        :param request: the message received
        :type request: dict()
        :param dictkeys: The keys that must exist in the returning message
        :type dictkeys: set()
        :param dictkeyvals: The key:val pairs that must exist ine the returning message
        :param dictkeyvals: disct()

        '''
        j_reply = self.messaging_req.send_request(category, action, request)
        reply = json.loads(j_reply)
        #print("receive reply : %s" % reply)
        res = True
        if "error" in reply['content']:
            res = False
        if dictkeys != None:
            for mykey in dictkeys :
                #print("check key %s" % mykey)
                if mykey not in reply['content'] :
                    #print("missing key %s" % mykey)
                    res = False
        if dictkeyvals != None:
            for mykey in dictkeyvals :
                #print("check keyval %s" % mykey)
                if mykey not in reply['content'] :
                    #print("missing keyval %s" % mykey)
                    res = False
                elif reply['content'][mykey] != dictkeyvals[mykey]:
                    #print("bad value %s for keyval %s" % (dictkeyvals[mykey],mykey))
                    res = False
        return res

    def setUp(self):
        #global sendrequest
        #self.__sendrequest = sendrequest
        self.messaging_req = MessagingReq()
        self.category = "plugin.earth.admin"

class GeneralTestCase(PluginTestCase):

    def test_010_check_zmq(self):
        action = "check"
        request = {}
        keys = None
        keyvalss = {'check' : 'ok'}
        self.assertTrue(self.send_request(self.category, action, request, keys, keyvalss))

    def test_020_badaction_zmq(self):
        action = "badaction"
        request = {}
        keys = None
        keyvalss = None
        self.assertFalse(self.send_request(self.category, action, request, keys, keyvalss))

    def test_050_gateway(self):
        action = "gateway"
        request = {}
        keys = ['host', 'type-list', 'stat-list', 'cmd-list', 'act-list', 'param-list']
        keyvalss = {"gateway" : "Domogik Earth"}
        self.assertTrue(self.send_request(self.category, action, request, keys, keyvalss))

    def test_080_memory(self):
        action = "memory"
        request = {}
        keys = ['memory', 'events', 'store', 'datafiles', 'zmq']
        keyvalss = None
        self.assertTrue(self.send_request(self.category, action, request, keys, keyvalss))

if __name__ == '__main__':

    sendrequest = MessagingReq()

    #unittest.main()
    suite = unittest.TestLoader().loadTestsFromTestCase(GeneralTestCase)
    #suite.addTests(unittest.TestLoader().loadTestsFromTestCase(DawnDuskTestCase))
    #suite.addTests(unittest.TestLoader().loadTestsFromTestCase(MoonPhasesTestCase))
    unittest.TextTestRunner(verbosity=3).run(suite)

