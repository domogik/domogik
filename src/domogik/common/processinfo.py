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
from __future__ import absolute_import, division, print_function, unicode_literals
import psutil
import time
from domogik.xpl.common.xplconnector import XplTimer
import threading
import traceback
import sys
from domogik import __version__ as domogik_version
import platform
from subprocess import Popen, PIPE
import os

class ProcessInfo():
    """ This class get informations about a process :
        cpu usage, memory usage, etc.
    """

    def __init__(self, pid, component_id, component_version, interval = 0, callback = None, log = None, stop = None):
        """ Init object
            @param pid : process identifier
            @param component_id : component id
            @param interval : time between looking for values
            @param callback : function to call to give values
               callback input : {"cpu_usage" : 33, ...}
            @param log : logger
            @param stop : event
        """
        # init vars
        self.psutil_version = psutil.__version__
        self.python_version = "{0}.{1}".format(sys.version_info[0], sys.version_info[1])
        self.pid = None
        self.component_id = component_id
        self.component_version = component_version
        self._callback = callback
        self._interval = interval
        self.log = log
        self._stop = stop
        # check pid exists
        if not psutil.pid_exists(pid):
            self.log.warning(u"No process '{0}' exists".format(pid))
            return
        # create psutil object
        self.p = psutil.Process(pid)
        self.pid = self.p.pid
        self.platform = platform.machine()
        self.num_core = psutil.cpu_count()
        self.git_branch = self.get_git_branch()
        self.git_revision = self.get_git_revision()
        self._start_time = 0

    def get_git_branch(self):
        """ If the current process file source is part of a git repo, return information (branch)
            Else, return an empty string
        """

        # TODO : improve if possible
        # dirty trick...
        # the manager is run from init.d by dmg_manager located in /usr/local/bin. So we can't find the manager.py path...
        # So we use the processinfo module path which is in the same git repo as manager.py
        if self.component_id == "core-manager":
            path = os.path.dirname(os.path.realpath(__file__))
        else:
            path = os.path.dirname(os.path.realpath(sys.argv[0]))
        cmd = 'cd "{0}" ; echo "$(git rev-parse --abbrev-ref HEAD 2>/dev/null)"'.format(path)
        sp = Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE)
        out, err = sp.communicate()
        return out.strip()

    def get_git_revision(self):
        """ If the current process file source is part of a git repo, return information (rev)
            Else, return an empty string
        """
        # TODO : improve if possible
        # dirty trick...
        # the manager is run from init.d by dmg_manager located in /usr/local/bin. So we can't find the manager.py path...
        # So we use the processinfo module path which is in the same git repo as manager.py
        if self.component_id == "core-manager":
            path = os.path.dirname(os.path.realpath(__file__))
        else:
            path = os.path.dirname(os.path.realpath(sys.argv[0]))
        cmd = 'cd "{0}" ; echo "$(git rev-parse --short HEAD 2>/dev/null)"'.format(path)
        sp = Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE)
        out, err = sp.communicate()
        return out.strip()


    def start(self):
        """ Get values each <interval> seconds while process is up
        """
        if self.pid == None:
            return
        self._start_time = time.time()
        while not self._stop.isSet():
            self._get_values()
            self._stop.wait(self._interval)

    def _get_values(self, raw = False):
        """ Get usefull values and put them in a dictionnary
            @param raw : True : return raw values. False : return values in Mo
        """
        try:
            # check process status
            if not psutil.pid_exists(self.pid):
                self.log.warning(u"Process '{0}' doesn't exists anymore : stop watching for it".format(self.pid))
                self.stop.set()
                return
            # cpu info
            cpu_percent = round(self.p.cpu_percent(), 1)
            num_threads = self.p.num_threads()
            num_fds = self.p.num_fds()
            # get memory info and set them in Mbyte
            memory_info = self.p.memory_info()
            if raw == False:
                divisor = 1024 * 1024
            else:
                divisor = 1
            memory_total_phymem = round(psutil.virtual_memory()[0] / divisor, 0)
            memory_rss = round(memory_info[0] / divisor, 1)
            memory_vsz = round(memory_info[1] / divisor, 1)
            memory_percent = round(self.p.memory_percent(),1)
            self.log.debug(u"Process informations|python_version={8}|psutil_version={0}|domogik_version={9}|component={1}|component_version={12}|pid={2}|cpu_percent_usage={3}|memory_total={4}|memory_percent_usage={5}|memory_rss={6}|memory_vsz={7}|num_threads={10}|num_file_descriptors_used={11}|platform={13}|num_core={14}|git_branch={15}|git_revision={16}".format(self.psutil_version, self.component_id, self.pid, cpu_percent, memory_total_phymem, memory_percent, memory_rss, memory_vsz, self.python_version, domogik_version, num_threads, num_fds, self.component_version, self.platform, self.num_core, self.git_branch, self.git_revision))
            if self._callback != None:
                # the domogik installation id (key 'id') will be filled by the manager or any other component which will process the below data
                data = {
                         'tags' : {
                             'python_version' : self.python_version,
                             'psutil_version' : self.psutil_version,
                             'domogik_version' : domogik_version,
                             'component' : self.component_id,
                             'component_version' : self.component_version,
                             'platform' : self.platform,
                             'num_core' : self.num_core,
                             'git_branch' : self.git_branch,
                             'git_revision' : self.git_revision
                         },
                         'measurements' : {
                             'unit' : 1,                               # this one is used to count items on grafana side
                             'cpu_percent_usage' : cpu_percent,
                             'memory_total' : memory_total_phymem,
                             'memory_percent_usage' : memory_percent,
                             'memory_rss' : memory_rss,
                             'memory_vsz' : memory_vsz,
                             'num_threads' : num_threads,
                             'num_file_descriptors_used' : num_fds
                         },
                         'start_timestamp' : self._start_time,
                         'timestamp' : time.time()
                       }
                self._callback(self.pid, data)
        except:
            self.log.warning(u"Process informations for client not working. Psutil version='{0}'. The error is : {1}".format(self.psutil_version, traceback.format_exc()))

def display(pid, data):
    print(u"DATA ({0}) = {1}".format(pid, str(data)))
