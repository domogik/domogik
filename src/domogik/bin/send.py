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

Plugin purpose
==============

Send xPL message from the shell

Implements
==========

- Sender.__init__(self, schema=None, message=None)
- Sender.parse_parameters(self)
- Sender.forge_message(self)
- Sender.usage(self)

@author: Maxence Dunnewind <maxence@dunnewind.net>
@copyright: (C) 2007-2012 Domogik project
@license: GPL(v3)
@organization: Domogik
"""
from __future__ import absolute_import, division, print_function, unicode_literals
from domogik.xpl.common.xplmessage import XplMessage
from domogik.xpl.common.plugin import XplPlugin
from argparse import ArgumentParser


class Sender(XplPlugin):
    ''' Send an xpl message
    usage : sendXPL.py message_type message_contents"
    message_type: Type of the message, must correspond to one of the supported schemas
    message_contents: comma separated pairs key=value that will be put in message
    '''

    supported_schemas = ["datetime.basic", "dawndusk.request", "x10.basic",
                         "sensor.basic", "domogik.system","domogik.config"]

    def __init__(self):
        parser = ArgumentParser()
        parser.add_argument(dest="type", help="XPL message type.")
        parser.add_argument(dest="schema", help="XPL message schema.")
        parser.add_argument(dest="message", help="XPL message data, comma seperated list (key=val,key2=val2).")
        parser.add_argument("-t", "--target", dest="target", default=None, help="XPL message target.")
        parser.add_argument("-s", "--source", dest="source", default=None, help="XPL message source.")
        XplPlugin.__init__(self, name = 'send', daemonize = False, parser = parser, nohub = True)
        mess = self.forge_message()
        self.log.debug(u"Send message : {0}".format(mess))
        self.myxpl.send(mess)
        self.force_leave()


    def forge_message(self):
        '''
        Create the message based on script arguments
        '''
        message = XplMessage()
        message.set_type(self.options.type)
        if self.options.source != None:
            print(u"Source forced : {0}".format(self.options.source))
            message.set_source(self.options.source)
        if self.options.target != None:
            print(u"Target forced : {0}".format(self.options.target))
            message.set_target(self.options.target)
        message.set_schema(self.options.schema)
        datas = self.options.message.split(',')
        for data in datas:
            if "=" not in data:
                self.log.error(u"Bad formatted commands. Must be key=value")
                self.usage()
                exit(4)
            else:
                message.add_data({data.split("=",1)[0].strip() :  data.split("=",1)[1].strip()})
        return message

    def usage(self):
        ''' Display script usage
        '''
        print(u"""\
usage : sendXPL.py message_type message_contents"
\tmessage_type: Type of the message, must correspond to one of the supported \
schemas
\tmessage_contents: comma separated pairs key=value that will be put in message
\tExample (x10): ./send.py xpl-cmnd x10.basic "device=a1,command=on"
""")

def main():
    Sender()

if __name__ == "__main__":
    main()
