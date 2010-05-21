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

Mock for X10 event on x10 network

Implements
==========

X10EvtMock.__init__


@author: Fritz <fritz.smh@gmail.com>
@copyright: (C) 2007-2009 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

from domogik.xpl.common.xplconnector import Listener
from domogik.xpl.common.plugin import XplPlugin, xPLResult
from domogik.xpl.common.xplmessage import XplMessage
from optparse import OptionParser




class X10EvtMock(XplPlugin):
    ''' 
    '''

    def __init__(self):
        '''
        '''

        # Check parameters 
        parser = OptionParser("Usage : %prog --command <command> [--device <device> | --house <house>] [--level <level>]")
        parser.add_option("--command", action="store", dest="command", type="string", \
                help="Command to send")
        parser.add_option("--house", action="store", dest="house", type="string", \
                help="House code [A-P]")
        parser.add_option("--device", action="store", dest="device", type="string", \
                help="Device code [A-P1-16]")
        parser.add_option("--level", action="store", dest="level", type="string", \
                help="Level (0...100)")

        XplPlugin.__init__(self, name = "x10evt", parser = parser)

        # Logger init
        self._log = self.get_my_logger()
        self._log.info("Launch x10 event mock for command=%s, house=%s, device=%s, level=%s" % (self.options.command, self.options.house, self.options.device, self.options.level))

        
        mess = XplMessage()
        mess.set_type('xpl-trig')
        mess.set_schema('x10.basic')
        if self.options.command != None:
            mess.add_data({'command' :  self.options.command})
        if self.options.house != None:
            mess.add_data({'house' :  self.options.house})
        if self.options.device != None:
            mess.add_data({'device' :  self.options.device})
        if self.options.level != None:
            mess.add_data({'level' :  self.options.level})
        print "Send message : %s" % mess
        self._log.info("Send message : %s" % mess)
        self._myxpl.send(mess)


        self.force_leave()




if __name__ == "__main__":
    X10EvtMock()
