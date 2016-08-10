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

Module purpose
==============

CLass which get informations about a process : cpu, memory

Implements
==========

- class ProcessInfo

@author: Fritz <fritz.smh@gmail.com>
@copyright: (C) 2007-2012 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

import psutil
import time
from domogik.xpl.common.xplconnector import XplTimer
import threading

class ProcessInfo():
    """ This class get informations about a process :
        cpu usage, memory usage, etc.
    """

    def __init__(self, pid, client_id, interval = 0, callback = None, log = None, stop = None):
        """ Init object
            @param pid : process identifier
            @param client_id : client id
            @param interval : time between looking for values
            @param callback : function to call to give values
               callback input : {"cpu_usage" : 33, ...}
            @param log : logger
            @param stop : event
        """
        # init vars
        self.pid = None
        self.client_id = client_id
        self._callback = callback
        self._interval = interval
        self.log = log
        self._stop = stop
        # check pid exists
        if not psutil.pid_exists(pid):
            self.log.warning(u"No process '{0}' exists" .format(pid))
            return
        # create psutil object
        self.p = psutil.Process(pid)
        self.pid = self.p.pid

    def start(self):
        """ Get values each <interval> seconds while process is up
        """
        if self.pid == None:
            return
        while not self._stop.isSet():
            self._get_values()
            self._stop.wait(self._interval)

    def _get_values(self, raw = False):
        """ Get usefull values and put them in a dictionnary
            @param raw : True : return raw values. False : return values in Mo
        """
        # check process status
        if not psutil.pid_exists(self.pid):
            self.log.warning(u"Process '{0}' doesn't exists anymore : stop watching for it".format(self.pid))
            self.stop.set()
            return
        # cpu info
        cpu_percent = round(self.p.get_cpu_percent(), 1)
        # get memory info and set them in Mbyte
        memory_total_phymem = round(psutil.TOTAL_PHYMEM / (1024 * 1024), 0)
        memory_info = self.p.get_memory_info()
        if raw == False:
            divisor = 1024 * 1024
        else:
            divisor = 1
        memory_rss = round(memory_info[0] / divisor, 1)
        memory_vsz = round(memory_info[1] / divisor, 1)
        memory_percent = round(self.p.get_memory_percent(),1)
        values = {"client_id" : self.client_id,
                  "pid" : self.pid,
                  "cpu_percent" : cpu_percent,
                  "memory_total_phymem" : memory_total_phymem,
                  "memory_rss" : memory_rss,
                  "memory_vsz" : memory_vsz,
                  "memory_percent" : memory_percent,
	 }
        # TODO : add threads number
        self.log.debug(u"Process informations for client '{2}' with pid = '{0}' : {1}".format(self.pid, values, self.client_id))
        if self._callback != None:
            self._callback(self.pid, values)

def display(pid, data):
    print(u"DATA ({0}) = {1}".format(pid, str(data)))

if __name__ == "__main__":
    my_process = ProcessInfo(3529)
    #my_process.start()
