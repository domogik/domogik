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

xPL message encoder/decoder.

An xPL message looks like:

xpl-cmnd
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

The XplMessage object maps all values as object attributes:

- type (str)
- hop_count (int)
- source (str)
- source_vendor_id (str)
- source_device_id (str)
- source_instance_id (str)
- target (str)
- target_vendor_id (str)
- target_device_id (str)
- target_instance_id (str)
- schema (str)
- schema_class (str)
- schema_type (str)
- data (OrderedDict)

It is possible to build a message from a network packet or from scratch.
It is also possible to create a network packet from the message.

More informations are available here:

  U{http://wiki.xplproject.org.uk/index.php/XPL_Specification_Document}

Implements
==========

- XplMessage

@author:Frédéric Mantegazza <frederic.mantegazza@gbiloba.org>
@author: Maxence Dunnewind <maxence@dunnewind.net>
@copyright: (C) 2008-2009 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

import re
import copy

from domogik.common.dmg_exceptions import XplMessageError
from domogik.common.ordereddict import OrderedDict

REGEXP_TYPE = r"""(?P<type_>xpl-cmnd | xpl-trig | xpl-stat)
              """
REGEXP_HOP_COUNT = r"""(?P<hop_count>[1-9]{1})$
                   """
REGEXP_SOURCE = r"""(?P<source>
                        (?P<source_vendor_id>[a-z, 0-9]{1,8})
                        -
                        (?P<source_device_id>[a-z, 0-9, _]{1,8})
                        \.
                        (?P<source_instance_id>[a-z, 0-9, \-]{1,16})$
                    )
                """
REGEXP_TARGET = r"""(?P<target>
                        (?:
                            (?P<target_vendor_id>[a-z, 0-9]{1,8})
                            -
                            (?P<target_device_id>[a-z, 0-9]{1,8})
                            \.
                            (?P<target_instance_id>[a-z, 0-9, \-]{1,16})$
                        ) |
                        \*
                    )
                """
REGEXP_SCHEMA = r"""(?P<schema>
                        (?P<schema_class>[a-z, 0-9, \-]{1,8})
                        \.
                        (?P<schema_type>[a-z, 0-9, \-]{1,8})$
                    )
                """
REGEXP_DATA = r"""(?P<data>(?:.*=.*\n)+)
              """
REGEXP_SINGLE_DATA = r"""(?P<data>
                             (?P<data_name>[a-z, 0-9, \-]{1,16})
                             =
#                             (?P<data_value>[a-z, A-Z, 0-9, \-, \., \/, _]{1,128})$  # [32-126] allowed!
                             (?P<data_value>[a-z, A-Z, 0-9, \!, \", \#, \$, \%, \
                                     \&, ', \(, \), \*, \+, \,, \-, \., \/, :, ;, \<, \>, ?, \=, \
                                     \{, \}, |\, \~, \\, \[, \], \@, _]{1,128})$  # [32-126] allowed!
                         )
                     """
REGEXP_GLOBAL = r"""(?P<type_>.*)\n
                    \{\n
                    hop=(?P<hop_count>.*)\n
                    source=(?P<source>.*)\n
                    target=(?P<target>.*)\n
                    \}\n
                    (?P<schema>.*)\n
                    \{\n
                    (?P<data>.*)\n
                    \}
                """


class XplMessage(object):
    """ xPL Message facility.

    XplMessage is the object for data send/received on the network.
    """
    __regexp_type = re.compile(REGEXP_TYPE, re.UNICODE | re.VERBOSE)
    __regexp_hop_count = re.compile(REGEXP_HOP_COUNT, re.UNICODE | re.VERBOSE)
    __regexp_source = re.compile(REGEXP_SOURCE, re.UNICODE | re.VERBOSE)
    __regexp_target = re.compile(REGEXP_TARGET, re.UNICODE | re.VERBOSE)
    __regexp_schema = re.compile(REGEXP_SCHEMA, re.UNICODE | re.VERBOSE)
    __regexp_data = re.compile(REGEXP_DATA, re.UNICODE | re.VERBOSE)
    __regexp_single_data = re.compile(REGEXP_SINGLE_DATA, re.UNICODE | re.VERBOSE)
    __regexp_global = re.compile(REGEXP_GLOBAL, re.DOTALL | re.UNICODE | re.VERBOSE)

    def __init__(self, packet=None):
        """ Message object.

        Create Message instance from a message string and check if the
        structure is correct. Raise exception if it is not
        The message can be None (to allow building a message)

        @param packet : message packet, as sent on the network
        @type packet: str
        """
        super(XplMessage, self).__init__()
        self.type = ""
        self.hop_count = 1
        self.source = ""
        self.source_vendor_id = ""
        self.source_device_id = ""
        self.source_instance_id = ""
        self.target = ""
        self.target_vendor_id = ""
        self.target_device_id = ""
        self.target_instance_id = ""
        self.schema = ""
        self.schema_class = ""
        self.schema_type = ""
        self.data = OrderedDict()
        if packet is not None:
            self.from_packet(packet)

    def __str__(self):
        return self.to_packet()

    def __parse_data(self, data):
        """ Parse message data.

        The data are added to existing ones.

        @param data: message data, as "<name1>=>value1>\n<name2>=<value2>\n..."
        @type data: str

        @raise XplMessageError: invalid data

        @todo: use OrderedDict for data storage
        """
        match_data = XplMessage.__regexp_data.match(data)
        if match_data is None:
            raise XplMessageError("Invalid data")
        match_data_dict = match_data.groupdict()
        data_list = match_data_dict['data'].split('\n')
        for data_ in data_list:
            if data_:
                self.__parse_single_data(data_)

    def __parse_single_data(self, data):
        """ Parse single message data.

        The data are added to existing ones.

        @param data: single message data, as "<name>=<value>"
        @type data: str

        @raise XplMessageError: invalid data
        """
        match_single_data = XplMessage.__regexp_single_data.match(data)
        if match_single_data is None:
            raise XplMessageError("Invalid data (%s)" % data)
        match_single_data_dict = match_single_data.groupdict()
        #self.data.append((match_single_data_dict['data_name'], match_single_data_dict['data_value']))
        key = match_single_data_dict['data_name']
        self.data[key] = match_single_data_dict['data_value']

    def set_type(self, type_):
        """ Set the message type.

        @param type_: message type, in ('xpl-stat', 'xpl-trig', 'xpl-cmnd')
        @type type_: str

        @raise XplMessageError: invalid type
        """
        match_type = XplMessage.__regexp_type.match(type_)
        if match_type is None:
            raise XplMessageError("Invalid type (%s)" % type_)
        self.type = type_

    def set_hop_count(self, hop_count):
        """ Set hop count value.

        @param hop_count: hop count
        @type hop_count: int or str

        @raise XplMessageError: invalid hop count value
        """
        match_hop_count = XplMessage.__regexp_hop_count.match(str(hop_count))
        if match_hop_count is None:
            raise XplMessageError("Invalid hop count value (%d)" % int(hop_count))
        self.hop_count = int(hop_count)

    def inc_hop_count(self):
        """ Increment hop count value.

        @raise XplMessageError: exceeded hop count value
        """
        hop_count = self.hop_count + 1
        match_hop_count = XplMessage.__regexp_hop_count.match(str(hop_count))
        if match_hop_count is None:
            raise XplMessageError("Exceeded hop count value (%s)" % str(hop_count))
        self.hop_count = hop_count

    def set_source(self, source):
        """ Set source.

        @param source: message source
        @type source: str

        @raise XplMessageError: invalid source
        """
        match_source = XplMessage.__regexp_source.match(source)
        if match_source is None:
            raise XplMessageError("Invalid source (%s)" % source)
        match_source_dict = match_source.groupdict()
        for key, value in match_source_dict.iteritems():
            setattr(self, key, value)

    def set_target(self, target):
        """ Set target.

        @param target: message target
        @type targer: str

        @raise XplMessageError: invalid target
        """
        match_target = XplMessage.__regexp_target.match(target)
        if match_target is None:
            raise XplMessageError("Invalid target (%s)" % target)
        match_target_dict = match_target.groupdict()
        for key, value in match_target_dict.iteritems():
            setattr(self, key, value)

    def set_header(self, hop_count=None, source=None, target=None):
        """ Set the message header.

        @param hop_count: hop count
        @type hop_count: int

        @param source: message source
        @type source: str

        @param target: message target
        @type targer: str
        """
        if hop_count is not None:
            self.set_hop_count(hop_count)
        if source is not None:
            self.set_source(source)
        if target is not None:
            self.set_target(target)

    def set_schema(self, schema):
        """ Set message schema.

        @param schema: message schema
        @type schema: str

        @raise XplMessageError: invalid schema
        """
        match_schema = XplMessage.__regexp_schema.match(schema)
        if match_schema is None:
            raise XplMessageError("Invalid schema (%s)" % schema)
        match_schema_dict = match_schema.groupdict()
        for key, value in match_schema_dict.iteritems():
            setattr(self, key, value)

    def add_single_data(self, name, value):
        """ Add a single message data.

        @param name: data name
        @type name: str

        @param value: data value
        @type value: any
        """
        data_str = "%s=%s" % (name, value)
        self.__parse_single_data(data_str)

    def add_data(self, data):
        """ Add message data to the existing ones.

        First build data as str, to be parsed by the regexp.

        @param data: message data, as name/value pairs
        @type data: dict or L{OrderedDict}
        """
        for name, value in data.iteritems():
            self.add_single_data(name, value)

    def set_data(self, data):
        """ Set message data, replacing previous ones. ???

        First build data as str, to be parsed by the regexp.

        @param data: message data, as name/value pairs
        @type data: dict or L{OrderedDict}
        """
        data_backup = copy.deepcopy(self.data)
        try:
            self.data = OrderedDict()
            self.add_data(data)
        except XplMessageError:
            self.data = copy.deepcopy(data_backup)
            raise

    def clear_data(self):
        """ Clear the message data.
        """
        self.data = OrderedDict()

    def from_packet(self, packet):
        """ Decode message from given packet.

        @param packet: message packet, as sent on the network
        @type packet: str

        @raise XplMessageError: the message packet is incorrect

        @raise XplMessageError: invalid message packet
        """
        match_global = XplMessage.__regexp_global.match(packet)
        if match_global is None:
            raise XplMessageError("Invalid message packet")
        else:
            match_global_dict = match_global.groupdict()
            self.set_type(match_global_dict['type_'])
            self.set_hop_count(match_global_dict['hop_count'])
            self.set_source(match_global_dict['source'])
            self.set_target(match_global_dict['target'])
            self.set_schema(match_global_dict['schema'])
            self.data = OrderedDict()
            data = match_global_dict['data'] + '\n'  # The global match remove the last '\n'
            self.__parse_data(data)

    def to_packet(self):
        """ Convert the message to packet.

        @return: message packet, as sent on the network
        @rtype: str
        """
        packet = "%s\n" % self.type
        packet += "{\n"
        packet += "hop=%d\n" % self.hop_count
        packet += "source=%s\n" % self.source
        packet += "target=%s\n" % self.target
        packet += "}\n"
        packet += "%s\n" % self.schema
        packet += "{\n"
        for key, value in self.data.iteritems():
            packet += "%s=%s\n" % (key, value)
        packet += "}\n"

        return packet

    def is_valid(self):
        """ Check if the message is valid.

        @return: True if message is valid, False otherwise
        @rtype: bool
        """
        try:
            self.from_packet(self.to_packet())
        except XplMessageError:
            return False
        else:
            return True
