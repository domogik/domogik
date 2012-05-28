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
XPL Cron server.

Implements
==========
class CronHelpers

@author: Sébastien Gallet <sgallet@gmail.com>
@copyright: (C) 2007-2012 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

from domogik_packages.xpl.lib.cron_tools import CRONERRORS

class CronHelpers():
    """
    Encapsulate the helpers
    """

    def __init__(self, log, jobs):
        """
        Initialise the helper class
        """
        self._log = log
        self._jobs = jobs


    def helper_list(self, params={}):
        """
        List all devices
        """
        self._log.debug("helper_list : Start ...")
        data = []
        if "which" in params:
            if params["which"] == "devices":
                data.append("List all devices :")
                data.extend(self._jobs.get_list(True))
            elif params["which"] == "aps":
                data.extend(self._jobs.get_ap_list(True))
            else:
                data.append("Bad parameter")
        else:
            data.append("No ""which"" parameter found")
        self._log.debug("helper_list : Done")
        return data

    def helper_memory(self, params={}):
        """
        Return memory usage.
        """
        self._log.debug("helper_memory : Start ...")
        data = []
        data.append("Memory use : ")
        data.extend(self._jobs.memory_usage(0))
        self._log.debug("helper_memory : Done ...")
        return data

    def helper_info(self, params={}):
        """
        Return informations on a device
        """
        self._log.debug("helper_info : Start ...")
        data = []
        if "device" in params:
            device = params["device"]
            data.append("Informations on device %s :" % device)
            if device in self._jobs.data:
                data.append(" Current state : %s" % \
                    (self._jobs.data[device]['current']))
                data.append(" Device type : %s" % \
                    (self._jobs.data[device]['devicetype']))
                data.append(" Uptime : %s" % (self._jobs.get_up_time(device)))
                data.append(" Runtime : %s" % (self._jobs.get_run_time(device)))
                data.append(" #Runtimes : %s" % (self._jobs.get_runs(device)))
                data.append(" #APScheduler jobs : %s" % \
                    (self._jobs.get_ap_count(device)))
            else:
                data.append(" Device not found")
        else:
            data.append("No ""device"" parameter found")
        self._log.debug("helper_info : Done")
        return data

    def helper_stop(self, params={}):
        """
        Stop a device
        """
        self._log.debug("helper_stop : Start ...")
        data = []
        if "device" in params:
            device = params["device"]
            data.append("Stop device %s :" % device)
            if device in self._jobs.data:
                data.append(" Current state : %s" % \
                    (self._jobs.data[device]['current']))
                ret = self._jobs.stop_job(device)
                data.append(" Return of the command : %s" % \
                    (CRONERRORS[ret]))
                data.append(" Current state : %s" % \
                    (self._jobs.data[device]['current']))
                data.append(" #APScheduler jobs : %s" % \
                    (self._jobs.get_ap_count(device)))
            else:
                data.append(" Device not found")
        else:
            data.append("No ""device"" parameter found")
        self._log.debug("helper_stop : Done")
        return data

    def helper_resume(self, params={}):
        """
        Resume a device
        """
        self._log.debug("helper_resume : Start ...")
        data = []
        if "device" in params:
            device = params["device"]
            data.append("Resume device %s :" % device)
            if device in self._jobs.data:
                data.append(" Current state : %s" % \
                    (self._jobs.data[device]['current']))
                ret = self._jobs.resume_job(device)
                data.append(" Return of the command : %s" % \
                    (CRONERRORS[ret]))
                data.append(" Current state : %s" % \
                    (self._jobs.data[device]['current']))
                data.append(" #APScheduler jobs : %s" % \
                    (self._jobs.get_ap_count(device)))
            else:
                data.append(" Device not found")
        else:
            data.append("No ""device"" parameter found")
        self._log.debug("helper_resume : Done")
        return data

    def helper_halt(self, params={}):
        """
        Halt a device
        """
        self._log.debug("helper_halt : Start ...")
        data = []
        if "device" in params:
            device = params["device"]
            data.append("Halt device %s :" % device)
            if params["device"] in self._jobs.data:
                data.append(" Current state : %s" % \
                    (self._jobs.data[device]['current']))
                ret = self._jobs.halt_job(device)
                data.append(" Return of the command : %s" % \
                    (CRONERRORS[ret]))
                data.append(" Current state : %s" % ("halted"))
            else:
                data.append(" Device not found")
                data.append(" Current state : %s" % ("halted"))
        else:
            data.append("No ""device"" parameter found")
        self._log.debug("helper_halt : Done")
        return data
