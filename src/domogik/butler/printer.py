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

This library is part of the butler

Implements
==========


@author: Fritz SMH <fritz.smh at gmail.com>
@copyright: (C) 2007-2017 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

import traceback
from subprocess import Popen, PIPE
import tempfile

def send_to_printer(log, data):
    if log == None:
        log = Log()
    tmp = tempfile.NamedTemporaryFile(delete=False)
    try:
        tmp.write(data)
        tmp.close()
        # TODO : grab from config
        cmd = 'lp -h 192.168.1.10 -d HP_Officejet_Pro_8600 {1}'.format(data, tmp.name)
        print( cmd)
        subp = Popen(cmd,
                     shell=True)
        pid = subp.pid
        subp.communicate()
        log.info(u"Printing action send to printer!")
        return True
    except:
        log.error(u"Error while printing. The error is : {0}".format(traceback.format_exc()))
        return False



class Log:
    def __init__(self):
        pass
    
    def info(self, msg):
        print(msg)
    
    def debug(self, msg):
        print(msg)
    
    def warning(self, msg):
        print(msg)
    
    def error(self, msg):
        print(msg)

if __name__ == "__main__":
    l = Log()
    send_to_printer(l, "hello domogik")

