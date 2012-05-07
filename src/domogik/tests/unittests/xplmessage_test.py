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

Plugin purpose
==============

Unit tests.

Implements
==========

- XplMessageTest

@author:Frédéric Mantegazza <frederic.mantegazza@gbiloba.org>
@copyright: (C) 2012 Domogik project
@license: GPL(v3)
@organization: Domogik
"""
import unittest
import re

from domogik.common.dmg_exceptions import XplMessageError
from domogik.common.ordereddict import OrderedDict
from domogik.xpl.common.xplmessage import XplMessage


class XplMessageTest(unittest.TestCase):
    """ Test XplMessage class.
    """
    def setUp(self):
        """ Setup context.

        The context is setup before each call to a test method.
        """
        self.__xpl_message = XplMessage()

    def tearDown(self):
        """ clean context.

        The context is cleaned after each call of a test method.
        """
        del self.__xpl_message

    def test_set_type(self):
        """ Test XplMessage.set_type() method.
        """
        self.assertRaises(XplMessageError, self.__xpl_message.set_type, 'dummy')
        for type_ in ('xpl-cmnd', 'xpl-trig', 'xpl-stat'):
            self.__xpl_message.set_type(type_)
            self.assertEqual(self.__xpl_message.type, type_)

    def test_set_hop_count(self):
        """ Test XplMessage.set_hop_count() method.
        """
        self.assertRaises(XplMessageError, self.__xpl_message.set_hop_count, 0)
        for i in xrange(1, 10):
            self.__xpl_message.set_hop_count(i)
            self.assertEqual(self.__xpl_message.hop_count, i)
        self.assertRaises(XplMessageError, self.__xpl_message.set_hop_count, 10)

    def test_inc_hop_count(self):
        """ Test XplMessage.inc_hop_count() method.
        """
        for i in xrange(8):
            self.__xpl_message.inc_hop_count()
        self.assertRaises(XplMessageError, self.__xpl_message.inc_hop_count)

    def test_set_source(self):
        """ Test XplMessage.set_source() method.
        """

        # Check length
        self.assertRaises(XplMessageError, self.__xpl_message.set_source, "xxxxxxxxx-x.x")
        self.assertRaises(XplMessageError, self.__xpl_message.set_source, "x-xxxxxxxxx.x")
        self.assertRaises(XplMessageError, self.__xpl_message.set_source, "x-x.xxxxxxxxxxxxxxxxx")

        # Check format
        self.assertRaises(XplMessageError, self.__xpl_message.set_source, "dummy")
        self.assertRaises(XplMessageError, self.__xpl_message.set_source, "xPL-hal.myhouse")
        self.__xpl_message.set_source("xpl-xplhal.myhouse")
        self.assertEqual(self.__xpl_message.source, "xpl-xplhal.myhouse")
        self.assertEqual(self.__xpl_message.source_vendor_id, "xpl")
        self.assertEqual(self.__xpl_message.source_device_id, "xplhal")
        self.assertEqual(self.__xpl_message.source_instance_id, "myhouse")

    def test_set_target(self):
        """ Test XplMessage.set_target() method.
        """

        # Check length
        self.assertRaises(XplMessageError, self.__xpl_message.set_target, "xxxxxxxxx-xxx.xxx")
        self.assertRaises(XplMessageError, self.__xpl_message.set_target, "xxx-xxxxxxxxx.xxx")
        self.assertRaises(XplMessageError, self.__xpl_message.set_target, "xxx-xxx.xxxxxxxxxxxxxxxxx")

        # Check format
        self.assertRaises(XplMessageError, self.__xpl_message.set_target, "dummy")
        self.assertRaises(XplMessageError, self.__xpl_message.set_target, "xPL-hal.myhouse")
        self.__xpl_message.set_target("acme-cm12.server")
        self.assertEqual(self.__xpl_message.target, "acme-cm12.server")
        self.assertEqual(self.__xpl_message.target_vendor_id, "acme")
        self.assertEqual(self.__xpl_message.target_device_id, "cm12")
        self.assertEqual(self.__xpl_message.target_instance_id, "server")
        self.__xpl_message.set_target('*')
        self.assertEqual(self.__xpl_message.target, '*')
        self.assertEqual(self.__xpl_message.target_vendor_id, None)
        self.assertEqual(self.__xpl_message.target_device_id, None)
        self.assertEqual(self.__xpl_message.target_instance_id, None)

    def test_set_schema(self):
        """ Test XplMessage.set_schema() method.
        """

        # Check length
        self.assertRaises(XplMessageError, self.__xpl_message.set_schema, "xxxxxxxxx.xxx")
        self.assertRaises(XplMessageError, self.__xpl_message.set_schema, "xxx.xxxxxxxxx")
        self.assertRaises(XplMessageError, self.__xpl_message.set_target, "x10-basic")

        # Check format
        self.assertRaises(XplMessageError, self.__xpl_message.set_schema, "dummy")
        self.__xpl_message.set_schema("x10.basic")
        self.assertEqual(self.__xpl_message.schema, "x10.basic")
        self.assertEqual(self.__xpl_message.schema_class, "x10")
        self.assertEqual(self.__xpl_message.schema_type, "basic")

    def test_add_single_data(self):
        """ Test XplMessage.test_add_single_data() method.
        """

        # check lengths
        name = 'x' * 17
        value = "xxx"
        self.assertRaises(XplMessageError, self.__xpl_message.add_single_data, name, value)
        name = "xxx"
        value = 'x' * 129
        #self.assertRaises(XplMessageError, self.__xpl_message.add_single_data, name, value)

        # 

    def test_set_data(self):
        """ Test XplMessage.set_data() method.
        """
        self.__xpl_message.set_data({"command": "dim",
                                     "device": "a1",
                                     "level": "75"})
        self.assertEqual(self.__xpl_message.data, OrderedDict({"command": "dim",
                                                               "device": "a1",
                                                               "level": "75"}))

        # Check if correctly remove previous data
        self.__xpl_message.set_data({"command2": "dim",
                                     "device2": "a1",
                                     "level2": "75"})
        self.assertEqual(self.__xpl_message.data, OrderedDict({"command2": "dim",
                                                               "device2": "a1",
                                                               "level2": "75"}))

    def test_from_packet(self):
        """ Test the XplMessage.from_packet() method.
        """
        wrong_packet = \
"""xpl-cmnd
{
target=acme-cm12.server
}
{
command=dim
device=a1
level=75
}
"""
        self.assertRaises(XplMessageError, self.__xpl_message.from_packet, wrong_packet)

        packet = \
"""xpl-cmnd
{
hop=1
source=xpl-xplhal.myhouse
target=acme-cm12.server
}
x10.basic
{
command=dim
device=a1
level=75
}
"""
        self.__xpl_message.from_packet(packet)
        self.assertEqual(self.__xpl_message.type, 'xpl-cmnd')
        self.assertEqual(self.__xpl_message.hop_count, 1)
        self.assertEqual(self.__xpl_message.source, "xpl-xplhal.myhouse")
        self.assertEqual(self.__xpl_message.source_vendor_id, "xpl")
        self.assertEqual(self.__xpl_message.source_device_id, "xplhal")
        self.assertEqual(self.__xpl_message.source_instance_id, "myhouse")
        self.assertEqual(self.__xpl_message.target, "acme-cm12.server")
        self.assertEqual(self.__xpl_message.target_vendor_id, "acme")
        self.assertEqual(self.__xpl_message.target_device_id, "cm12")
        self.assertEqual(self.__xpl_message.target_instance_id, "server")
        self.assertEqual(self.__xpl_message.schema, "x10.basic")
        self.assertEqual(self.__xpl_message.schema_class, "x10")
        self.assertEqual(self.__xpl_message.schema_type, "basic")
        self.assertEqual(self.__xpl_message.data, OrderedDict({"command": "dim",
                                                               "device": "a1",
                                                               "level": "75"}))

    def testto_packet(self):
        """ Test XplMessage.to_packet() method.
        """
        packet = \
"""xpl-cmnd
{
hop=1
source=xpl-xplhal.myhouse
target=acme-cm12.server
}
x10.basic
{
command=dim
device=a1
level=75
}
"""
        self.__xpl_message.from_packet(packet)
        self.assertEquals(self.__xpl_message.to_packet(), packet)

    def test_is_valid(self):
        """ Test XplMessage.is_valid() method.
        """
        packet = \
"""xpl-cmnd
{
hop=1
source=xpl-xplhal.myhouse
target=acme-cm12.server
}
x10.basic
{
command=dim
device=a1
level=75
}
"""
        self.assertEquals(self.__xpl_message.is_valid(), False)
        self.__xpl_message.from_packet(packet)
        self.assertEquals(self.__xpl_message.is_valid(), True)


if __name__ == "__main__":
    unittest.main()
