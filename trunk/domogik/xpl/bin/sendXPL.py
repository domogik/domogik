#!/usr/bin/python
# -*- encoding:utf-8 -*-

# Copyright 2008 Domogik project

# This file is part of Domogik.
# Domogik is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# Domogik is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with Domogik.  If not, see <http://www.gnu.org/licenses/>.

# Author: Maxence Dunnewind <maxence@dunnewind.net>

# $LastChangedBy: maxence $
# $LastChangedDate: 2009-02-22 15:31:11 +0100 (dim. 22 févr. 2009) $
# $LastChangedRevision: 396 $

#This script use arguments from command line to forge & send a message
from domogik.xpl.lib.xplconnector import *
from domogik.xpl.lib.module import *
import optparse
from domogik.common.configloader import Loader
from domogik.common import logger


class Sender(xPLModule):

    supported_schemas = ["datetime.basic", "dawndusk.request", "x10.basic",
            "sensor.basic", "domogik.system"]

    def __init__(self, schema=None, message=None):
        xPLModule.__init__(self, name = 'send')
        self._schema = schema
        self._message = message
        cfgloader = Loader('send')
        self.__myxpl = Manager()
        self._log = self.get_my_logger()
        self.parse_parameters()
        mess = self.forge_message()
        self._log.debug("Send message : %s" % mess)
        self.__myxpl.send(mess)
        self.__myxpl.force_leave()

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
        if len(self._args) != 2:
            self.usage()
            exit(1)

        if self._args[0] not in self.supported_schemas:
            self._log.error("Schema %s not supported" % self._args[0])
            self.usage()
            exit(2)

    def forge_message(self):
        '''
        Create the message based on script arguments
        '''
        message = Message()
        message.set_type("xpl-cmnd")
        message.set_schema(self._args[0])
        datas = self._args[1].split(',')
        for data in datas:
            if "=" not in data:
                self._log.error("Bad formatted commands. Must be key=value")
                self.usage()
                exit(4)
            else:
                message.set_data_key(data.split("=")[0], data.split("=")[1])
        return message

    def usage(self):
        print """\
usage : send.py message_type message_contents"
\tmessage_type: Type of the message, must correspond to one of the supported \
schemas
\tmessage_contents: comma separated pairs key=value that will be put in message
\tExample (x10): ./send.py x10.basic "device=a1,command=on"
"""


if __name__ == "__main__":
    s = Sender()
    #s.parse_parameters()
