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
@copyright: (C) 2007-2012 Domogik project
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
                            (?P<target_device_id>[a-z, 0-9, _]{1,8})
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
#REGEXP_SINGLE_DATA = r"""(?P<data>
#                         (?P<data_name>[a-z, 0-9, \-]{1,16})
#                         =
#                         (?P<data_value>[a-z, A-Z, 0-9, \!, \", \#, \$, \%, \
#                             \&, ', \(, \), \*, \+, \,, \-, \., \/, :, ;, \<, \>, ?, \=, \
#                             \{, \}, |\, \~, \\, \[, \], \@, _].*)$  # [32-126] allowed!
#                         )
#                     """

REGEXP_SINGLE_DATA = r"""(?P<data>
                             (?P<data_name>[a-z0-9 ,-]{1,16})
                             =
                             (?P<data_value>[%s].*)$
                         )
                     """ % re.escape(''.join(chr(x) for x in xrange(32, 256)))


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
        if key in self.data:
            if type(self.data[key]) != list:
                v = self.data[key]
                self.data[key] = [v]
            self.data[key].append(match_single_data_dict['data_value'])
        else:
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
            if type(value) == list:
                for v in value:
                    packet += "%s=%s\n" % (key, v)
            else:
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


class FragmentedXplMessage(object):
    """ Defines a fragemented xPL Message
    """
    def __init__(self, fragment=None):
        """ Creates a FragmentedXplMessage instance and start to fill it with fragment
        @param uid : unique message identifier
        @param fragment : first fragment of the message
        @type fragment XplMessage
        """
        self._fragments = {}
        self._message_id = None
        self._fragment_count = 0
        self._mess_type = None
        self._mess_schema = None
        self._mess_from = None
        if fragment:
            self._init_from_fragment(fragment)
            self.add_fragment(fragment)

    def _init_from_fragment(self, fragment):
        """ Initialize the object with the first fragment
        @param fragment : fragment of the message
        @type fragment : XplMessage
        @warning the schema will be initialized only with the first fragment
        """
        ids = self._extract_ids(fragment)
        self._message_id = ids[2]
        self._fragment_count = int(ids[1])
        self._mess_type = fragment.type
        self._mess_from = fragment.source
        self._mess_to = fragment.target
        if "schema" in fragment.data:
            self._mess_schema = fragment.data["schema"]

    def add_fragment(self, fragment):
        """ Add a fragment to the message
        """
        ids = self._extract_ids(fragment)
        if (((not self._mess_schema) and (ids[0] == 1)) or not self._message_id):
            self._init_from_fragment(fragment)
        if ids[2] != self._message_id:
            raise ValueError("The message ID is not the same as previous fragments")
        if ids[1] != self._fragment_count:
            raise ValueError("The number of fragments is not the same as previous fragments")
        self._fragments[int(ids[0])] = fragment
        
    def _extract_ids(self, fragment):
        """ Extract message IDs from a fragment
        @param fragment : one fragment of the message
        @type fragment XplMessage
        
        @return a tuple with (fragment number, #of fragments, the message ID)
        @raise ValueError if no message ID can be extracted
        """
        if "partid" in fragment.data:
            partid = fragment.data["partid"]
            try:
                parts =  partid.split(':')
                f_id = parts[0].split('/')[0]
                f_total = parts[0].split('/')[1]
                m_id = parts[1]
            except:
                raise ValueError, "Can't parse partid"
            else:
                return (int(f_id), int(f_total), m_id)

    def generate_missing_request(self, ids=None):
        """ Generates an XplMessage to request the re-send of some fragments
        if ids is None, will request all the missing fragments
        @param ids : list of fragments'id to request
        @return XplMessage instance to request fragments or None if no fragment were already stored or if all were received
        """
        if ((self._fragment_count == 0) or (len(self._fragments) == self._fragment_count)):
            return None

        msg = XplMessage()
        msg.set_type("xpl-cmnd")
        msg.set_target(self._mess_from)
        msg.set_schema("fragment.request")
        msg.add_single_data("command","resend")
        msg.add_single_data("message",self._message_id)

        if ids:
            for i in ids:
                msg.add_single_data("part",str(i))
        else:
            for i in range(1, self._fragment_count + 1):
                if i not in self.fragments:
                    msg.add_single_data("part",str(i))
        return msg

    def build_message(self):
        """Build the XplMessage from all fragments
        @return None if not all fragments are received
        """
        if len(self._fragments) != self._fragment_count:
            return None

        msg = XplMessage()
        msg.set_type(self._mess_type)
        msg.set_schema(self._mess_schema)
        msg.set_source(self._mess_from)
        msg.set_target(self._mess_to)
        for i in range(1, self._fragment_count + 1):
            f = self._fragments[i]
            for d in f.data.keys():
                if d not in ["partid","schema"]:
                    msg.add_single_data(d, f.data[d])
        return msg

    @staticmethod
    def fragment_message(message, uid):
        """ Fill the instance with fragments from the message
        @param message: XplMessage instance to split
        @param uid : the unique ID that should identify this message
        @return an OrderedDict which contains all the fragments
        """
        #we use an OrderedDict to store messages until we know the total number of messages
        message_list = OrderedDict()
        msg = FragmentedXplMessage.__init_fragment(message, uid)
        base_len = len(msg.to_packet())
        f_id = 1
        for k in message.data:
            if type(message.data[k]) == list:
                for l in message.data[k]:
                    if not FragmentedXplMessage.__try_add_item_to_message(msg, k, l):
                        message_list[f_id] = msg
                        msg = FragmentedXplMessage.__init_fragment(message, uid)
                        FragmentedXplMessage.__try_add_item_to_message(msg, k, l)
                        f_id = f_id + 1
            else:
                if not FragmentedXplMessage.__try_add_item_to_message(msg, k, message.data[k]):
                    message_list[f_id] = msg
                    msg = FragmentedXplMessage.__init_fragment(message, uid)
                    FragmentedXplMessage.__try_add_item_to_message(msg, k, message.data[k])
                    f_id = f_id + 1
                    
        message_list[f_id] = msg
        return FragmentedXplMessage.__update_fragments_ids(message_list, uid)

    @staticmethod
    def __update_fragments_ids(fragment_list, uid):
        """ Update the id of all fragments to set the corect id/total nuber of fragments
        @param fragment_list : an Ordered list with all fragments
        @param uid : the unique ID that should identify this message
        @return The updated OrderedDict
        """
        l = len(fragment_list)
        for f in fragment_list:
            fragment_list[f].data["partid"] = "%s/%s:%s" % (f, l, uid)
        return fragment_list

    @staticmethod
    def __init_fragment(message, uid):
        """ Create a fragment message and init it from the provider XplMessage
        @param message : The message to init fragment from
        @param uid : the unique ID that should identify this message
        @return a new fragment
        """
        msg = XplMessage()
        msg.set_type(message.type)
        msg.set_schema("fragment.basic")
        msg.set_source(message.source)
        msg.set_target(message.target)
        msg.add_single_data("partid","##/##:%s" % uid) 
        msg.add_single_data("schema", message.schema)
        return msg

    @staticmethod
    def __try_add_item_to_message(message, item_k, item_v):
        """ Try to add an item to the message
        if the message len is < 1472 with the item, then add it
        else don't.
        @param message : The XplMessage to add the item to
        @param item_k : item key
        @param item_v : item value
        @return True if the item was correctly added, false otherwise
        """
        item = "%s=%s\n" % (item_k, item_v)
        if len(item) + len(message.to_packet()) < 1472:
            message.add_single_data(item_k, item_v)
            return True
        else:
            return False

