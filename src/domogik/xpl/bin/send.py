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
@copyright: (C) 2007-2009 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

from domogik.xpl.common.xplmessage import XplMessage
from domogik.xpl.common.plugin import XplPlugin
import optparse


class Sender(XplPlugin):
    ''' Send an xpl message
    usage : sendXPL.py message_type message_contents"
    message_type: Type of the message, must correspond to one of the supported schemas
    message_contents: comma separated pairs key=value that will be put in message
    '''

    supported_schemas = ["datetime.basic", "dawndusk.request", "x10.basic",
                         "sensor.basic", "domogik.system","domogik.config"]

    def __init__(self, schema=None, message=None):
        XplPlugin.__init__(self, name = 'send', daemonize = False)
        self._schema = schema
        self._message = message
        self._log = self.get_my_logger()
        self._args = []
        self._options = None
        self.parse_parameters()
        mess = self.forge_message()
        self._log.debug("Send message : %s" % mess)
        self._myxpl.send(mess)
        self.force_leave()

    def parse_parameters(self):
        '''
        Read parameters from command line and parse them
        '''
        if self._message != None and self._schema != None:
            self._options = None
            self._args = [self._schema, self._message]
        else:
            parser = optparse.OptionParser()
            parser.add_option("-d", "--dest", type="string",
                    dest="message_dest", default="broadcast")
            (self._options, self._args) = parser.parse_args()

        #Parsing of args
        if len(self._args) != 3:
            self.usage()
            exit(1)

       # if self._args[1] not in self.supported_schemas:
       #     self._log.error("Schema %s not supported" % self._args[0])
       #     self.usage()
       #     exit(2)

    def forge_message(self):
        '''
        Create the message based on script arguments
        '''
        message = XplMessage()
        message.set_type(self._args[0])
        message.set_schema(self._args[1])
        datas = self._args[2].split(',')
        for data in datas:
            if "=" not in data:
                self._log.error("Bad formatted commands. Must be key=value")
                self.usage()
                exit(4)
            else:
                message.add_data({data.split("=")[0] :  data.split("=")[1]})
        return message

    def usage(self):
        ''' Display script usage
        '''
        print """\
usage : sendXPL.py message_type message_contents"
\tmessage_type: Type of the message, must correspond to one of the supported \
schemas
\tmessage_contents: comma separated pairs key=value that will be put in message
\tExample (x10): ./send.py xpl-cmnd x10.basic "device=a1,command=on"
"""

def main():
    Sender()

if __name__ == "__main__":
    main()
