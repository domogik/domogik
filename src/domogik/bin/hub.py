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

xpl Hub

Implements
==========

@author: Fritz SMH <fritz.smh@gmail.com>
@copyright: (C) 2007-2012 Domogik project
@license: GPL(v3)
@organization: Domogik
"""


from optparse import OptionParser
from domogik.common import daemonize
from sys import stdout

# version
VERSION=1.0




#if __name__ == "__main__":
#    main()


def main():
    ### Options management
    parser = OptionParser()
    parser.add_option("-V", 
                      "--version", 
                      action="store_true", 
                      dest="display_version", 
                      default=False, 
                      help="Display the xPL hub version.")
    parser.add_option("-f", 
                      action="store_true", 
                      dest="run_in_foreground", 
                      default=False, 
                      help="Run the xPL hub in foreground, default to background.")
    (options, args) = parser.parse_args()
    if options.display_version:
        print(VERSION)
        sys.exit(0)
    if not options.run_in_foreground:
        daemon = True
        daemonize.createDaemon()

        #from twisted.internet.protocol import DatagramProtocol
        from twisted.internet import reactor
        #from twisted.python import log

    else:
        daemon = False
        #from twisted.internet.protocol import DatagramProtocol
        from twisted.internet import reactor
        #from twisted.python import log


    ### Launch the hub
    from domogik.xpl.lib.hub import Hub
    Hub(daemon)







if __name__ == "__main__":
    main()





#def main():
#    pass






