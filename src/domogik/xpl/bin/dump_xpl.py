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

Print all xPL traffic

Implements
==========

- Sniffer.__init__(self)
- Sniffer._sniffer_cb(self, message)


@author: Maxence Dunnewind <maxence@dunnewind.net>
@copyright: (C) 2007-2012 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

from domogik.xpl.common.xplconnector import Listener
from domogik.xpl.common.plugin import XplPlugin
import datetime
from time import localtime
from optparse import OptionParser

class Sniffer(XplPlugin):
    '''Sniff xpl network and dump all messages
    '''

    def __init__(self):
        parser = OptionParser()
        parser.add_option("-c", action="store_true", dest="compress", \
		default=False, help="Diaply data in a compress way")
        parser.add_option("-t", action="store", dest="xpltype", \
                default=None, type="string", \
                help="Filter messages on XPL message type")
        parser.add_option("-s", action="store", dest="xplsource", \
                default=None, type="string", \
                help="Filter messages on XPL source field")
        parser.add_option("-S", action="store", dest="xplschema", \
                default=None, type="string", \
                help="Filter messages on XPL schema field")
        parser.add_option("-i", action="store", dest="xplinstance", \
                default=None, type="string", \
                help="Filter messages on XPL instance")
        XplPlugin.__init__(self, name='dump_xpl', daemonize=False, \
                parser=parser)
        fil = {}
        if self.options.xpltype != None:
            fil['xpltype'] = self.options.xpltype
        if self.options.xplsource != None:
            fil['xplsource'] = self.options.xplsource
        if self.options.xplschema != None:
            fil['schema'] = self.options.xplschema
        if self.options.xplinstance != None:
            fil['xplinstance'] = self.options.xplinstance
        Listener(self._sniffer_cb, self.myxpl, filter=fil)
        self.enable_hbeat()

    def _sniffer_cb(self, message):
        '''
        Print received message
        '''
        if self.options.compress == False:
            print("%s - %s" % (datetime.datetime.now(), message))
            self.log.info("%s - %s" % (datetime.datetime.now(), message))
        else:
            ldt = localtime()
            date = "%s/%s/%s" % (ldt[0], self._format(ldt[1]), self._format(ldt[2]))
            time = "%s:%s:%s" % (self._format(ldt[3]), self._format(ldt[4]), self._format(ldt[5]))
            display = "%s" % time
            self.log.info("%s - %s" % (datetime.datetime.now(), message))
            print("%s - %s %s hop=%s source=%s target=%s" % (display,
                                                          message.type,
                                                          message.schema,
                                                          message.hop_count,
                                                          message.source,
                                                          message.target))
            idx = 0
            for elt in message.data:
                print("  %s=%s" % (elt, message.data[elt]))
                idx += 1
                if idx == 4:
                    print("  ...")
                    return

    def _format(self, number):
        '''
        Format the number
        '''
        if int(number) < 10:
            return "0%s" % number
        else:
            return number

def main():
    S = Sniffer()

if __name__ == "__main__":
    main()

