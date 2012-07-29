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

    def __init__(self):
        parser = optparse.OptionParser()
        parser.add_option("-t", "--target", type="string",
                dest="target", default=None)
        parser.add_option("-s", "--source", type="string",
                dest="source", default=None)
        XplPlugin.__init__(self, name = 'send', daemonize = False, parser = parser, nohub = True)
        mess = self.forge_message()
        self.log.debug("Send message : %s" % mess)
        self.myxpl.send(mess)
        self.force_leave()


    def forge_message(self):
        '''
        Create the message based on script arguments
        '''
        message = XplMessage()
        message.set_type(self.args[0])
        if self.options.source != None:
            print("Source forced : %s" % self.options.source)
            message.set_source(self.options.source)
        if self.options.target != None:
            print("Target forced : %s" % self.options.target)
            message.set_target(self.options.target)
        message.set_schema(self.args[1])
        datas = self.args[2].split(',')
        for data in datas:
            if "=" not in data:
                self.log.error("Bad formatted commands. Must be key=value")
                self.usage()
                exit(4)
            else:
                message.add_data({data.split("=",1)[0].strip() :  data.split("=",1)[1].strip()})
        return message

    def usage(self):
        ''' Display script usage
        '''
        print("""\
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
