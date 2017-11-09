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

Command line installer for packages

Implements
==========

- PackageInstaller

@author: Fritz SMH <fritz.smh@gmail.com>
@copyright: (C) 2007-2012 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

from domogik.common import logger
from domogik.common.database import DbHelper
from domogik.common.utils import is_already_launched
import traceback

class CronSystem():
    """ Package installer class
    """
    def __init__(self):
        """ Init
        """
        l = logger.Logger("core_cron", log_on_stdout=True)
        self.log = l.get_logger()
        withCache = is_already_launched(self.log, "core", "cachedb", False)
        self.db = DbHelper(use_cache=withCache[0])
        self.run()

    def run(self):
        self.log.info(u"START Cron system run")
        self._delete_devices()
        self._migrate_sensor()
        self.log.info(u"END   Cron system run")

    def _delete_devices(self):
        self.log.info(u"=> START device deleting")
        with self.db.session_scope():
            for dev in self.db.list_devices(d_state=u'delete'):
                try:
                    self.log.info(u"   => Deleting device '{0}' from plugin '{1}'".format(dev['name'], dev['client_id']))
                    self.db.del_device_real(dev['id'])
                except:
                    self.log.error(u"     Unable to delete the device. Please check the error message for the reason. Error is : {0}".format(traceback.format_exc()))
        self.log.info(u"=> END device deleting")

    def _migrate_sensor(self):
        self.log.info(u"=> START sensor migration")
        with self.db.session_scope():
            for sensor in self.db.get_migration_all_sensors():
                print sensor
        self.log.info(u"=> END sensor migration")

def main():
    cron = CronSystem()

if __name__ == "__main__":
    main()
