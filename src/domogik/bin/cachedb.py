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

Module purpose
==============

Miscellaneous utility database functions

Implements
==========


@author: Nicolas VIGNAL <nic84dev at gmail.com>
@copyright: (C) 2007-2012 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

from domogik.common.defaultloader import DefaultLoader
from domogik.common.configloader import Loader
from domogik.common import logger
from multiprocessing import Lock
from multiprocessing.managers import SyncManager, active_children, current_process
from threading import Thread

import signal
import sys
import os
import pwd
import time

CACHE_NAME = 'cachedb_api'

class CacheData(object):
    _devices_cache = []
    _to_update_devices = {}
    _lockList = Lock()

    _config_cache = {}
    _to_update_config = {}
    _lockConfig = Lock()

    def __init__(self):
        # Here you have to specify twice the logger name as two instances of DbHelper are created
        self.log = logger.Logger(CACHE_NAME).get_logger(CACHE_NAME)
        self.log.debug(u"Cache Data initialized")

# Devices list cache data
    def getDevices(self, client_id = None):
        with self._lockList :
            if client_id is not None :
                devices = []
                for dev in self._devices_cache:
                    if dev['client_id'] == client_id :
                      devices.append(dict(dev))
                self.log.debug(u"Get cache with {0} device(s) for client {1}".format(len(devices), client_id))
                return devices
            else :
                self.log.debug(u"Get cache with {0} device(s) for all clients".format(len(self._devices_cache)))
                return list(self._devices_cache)

    def upToDateDevices(self, client_id = None, device_id = None):
        with self._lockList :
            if device_id is not None :
                device_id = int(device_id)
                if device_id in self._to_update_devices :
                    return not self._to_update_devices[device_id]
                else :
                    return False
            elif client_id is not None :
                exist = False
                for dev in self._devices_cache:
                    if dev['client_id'] == client_id :
                        exist = True
                        uptodate = not self._to_update_devices[dev['id']]
                        if not uptodate: return False
                return exist
            else :
                if self._devices_cache is None or self._devices_cache == []:
                    self.log.debug(u"Cache is empty.")
                    return False
                for dev in self._devices_cache:
                    uptodate = not self._to_update_devices[dev['id']]
                    if not uptodate: return False
                return True
            return False

    def setDevices(self, device_list, source="undefined"):
        with self._lockList :
            self._devices_cache = device_list
            self._to_update_devices = {}
            for dev in self._devices_cache:
                self._to_update_devices[dev['id']] = False
            self.log.debug(u"Set cache with {0} device(s). Source : {1}".format(len(self._devices_cache), source))
            return True

    def updateDevices(self, device_list, client_id = None, device_id = None):
        with self._lockList :
            if device_id is not None : # Update one device of device_list
                device_id = int(device_id)
                for i in range(0, len(self._devices_cache)) :
                    if self._devices_cache[i]['id'] == device_id :
                        self._devices_cache[i] = device_list
                        self._to_update_devices[device_id] = False
                        self.log.debug(u"Update cache, mode device : {0}".format(device_id))
                        break
            elif client_id is not None : # Update by client
                for dev in list(self._devices_cache):
                    # 1st remove all devices for client (assume deleted device)
                    if dev['client_id'] == client_id :
                        self._devices_cache.remove(dev)
                        del(self._to_update_devices[dev['id']])
                self._devices_cache.extend(device_list)
                for dev in device_list :
                    self._to_update_devices[dev['id']] = False
                self.log.debug(u"Update cache for {0} device(s), mode client : {1}".format(len(device_list), client_id))
            else : #  Update all devices of device_list
                for dev_n in device_list :
                    for dev in self._devices_cache :
                        if dev['id'] == dev_n['id'] :
                            dev = dev_n
                            self._to_update_devices[dev['id']] = False
                self.log.debug(u"Update cache for {0}/{1} device(s), mode all of list.".format(len(device_list),len(self._devices_cache)))

    def markAsUpdatingDevices(self, client_id = None, device_id = None, sensor_id = None):
        with self._lockList :
            if sensor_id is not None :
                for dev in self._devices_cache :
                    for key in dev['sensors'] :
                        if dev['sensors'][key]['id'] == sensor_id :
                            self._to_update_devices[dev['id']] = True
#                            self.log.debug(u"Mark to update cache mode sensor : {0}".format(sensor_id))
                            break
            elif device_id is not None : # Mark one device
                device_id = int(device_id)
                for dev in self._devices_cache :
                    if dev['id'] == device_id :
                        self._to_update_devices[dev['id']] = True
#                        self.log.debug(u"Mark to update cache mode device : {0}".format(device_id))
                        break
            elif client_id is not None : # Mark devices by client
                for dev in self._devices_cache:
                    if dev['client_id'] == client_id :
                        self._to_update_devices[dev['id']] = True
#                self.log.debug(u"Mark to update cache mode client : {0}".format(client_id))
            else : #  Mark all devices
                for dev_n in self._devices_cache :
                    self._to_update_devices[dev['id']] = True
#                self.log.debug(u"Mark to update cache mode all clients")

# Plugin Config Cache Data

    def convert(self, data):
        """ Do some conversions on data
        """
        if data == "True":
            data = True
        if data == "False":
            data = False
        return data

    def _getConfigId(self, pl_id, pl_hostname):
        return u"{0}.{1}".format(pl_id, pl_hostname)

    def getConfig(self, pl_id, pl_hostname, key=None):
        with self._lockConfig :
            pId = self._getConfigId(pl_id, pl_hostname)
            if pId in self._config_cache :
                if key is not None :
                    for p in self._config_cache[pId] :
                        if p.key == key :
                            return p
                config = list(self._config_cache[pId])
                self.log.debug(u"Get cache config with {0} parameters(s) for client {1}".format(len(config), pId))
                return config
            else :
                self.log.debug(u"Get cache config don't known client {0}".format(pId))
                return []

    def setConfigData(self, config_list, pl_id, pl_hostname, source="undefined"):
        with self._lockConfig :
            pId = self._getConfigId(pl_id, pl_hostname)
            self._config_cache[pId] = config_list
            self._to_update_config[pId] = False
            self.log.debug(u"Set cache config with {0} parameters for client {1}. Source : {2}".format(len(self._config_cache[pId]), pId, source))
            return True

    def upToDateConfig(self, pl_id, pl_hostname):
        with self._lockConfig :
            pId = self._getConfigId(pl_id, pl_hostname)
            if pId in self._to_update_config :
                return not self._to_update_config[pId]
            return False

    def markAsUpdatingConfig(self, pl_id, pl_hostname):
        with self._lockConfig :
            pId = self._getConfigId(pl_id, pl_hostname)
            if pId in self._to_update_config :
                self._to_update_config[pId] = True
#                self.log.debug(u"Mark to update cache config for client {0}".format(pId))

class MyManager(SyncManager): pass

class WorkerCache(object):

    def __init__(self):
        print(u"+++++++++++++++++++++++ Init cache worker")
        ### First, check if the user is allowed to launch the plugin. The user must be the same as the one defined
        # in the file /etc/default/domogik : DOMOGIK_USER
        default = DefaultLoader()
        dmg_user = default.get("DOMOGIK_USER")
        logname = pwd.getpwuid(os.getuid())[0]
        if dmg_user != logname:
            print(u"ERROR : this Domogik part must be run with the user defined in /etc/default/domogik as DOMOGIK_USER : {0}".format(dmg_user))
            sys.exit(1)
        logg = logger.Logger(CACHE_NAME, use_filename="{0}".format(CACHE_NAME), log_on_stdout=True)
        self.log = logg.get_logger()

        self.log.info(u"Initializing cache worker :{0}".format(self))

        cfg = Loader('database')
        config = cfg.load()
        db_config = dict(config[1])
 
        port_c = 50001 if not 'portcache' in db_config else int(db_config['portcache'])

        self._cache = CacheData()
        MyManager.register('get_cache', callable=lambda:self._cache)
        MyManager.register('force_leave', callable=lambda:self.force_leave())
        self.cacheManager = MyManager(address=('localhost', port_c), authkey=b'{0}'.format(db_config['password']))
        self.cacheManager.start()
        self.log.info(u"Listening on port '{0}' [BIND]...".format(port_c))
        self._pPIDs = []
        for p in active_children():
            self._pPIDs.append(p.pid)
        self._pPIDs.append(current_process().pid)
        self._running = True
        self.log.info(u"Init cache worker done on Process IDs {0} :{1}".format(self._pPIDs, self))

    def force_leave(self):
        """ Stop manager cache
        """
        selfPID =  current_process().pid
        pPID = os.getppid()
        self.log.info(u"Call force_leave by kill parent process {0} and it self {1} : {2}".format(pPID, selfPID, self))
        # Killing all subProcess. Not really academic, but I d'ont find other way !"
        os.kill(int(pPID), signal.SIGKILL)
        os.kill(int(selfPID), signal.SIGKILL)

    def start(self):
        Thread(None,
                  self.__start,
                  "run_cache_forever",
                  (),
                  {}).start()

    def __start(self):
        self.log.info(u"Start loop forever")
        self._running = True
        while self._running :
            time.sleep(0.05)
        self.log.info(u"Loop forever stopped")


if __name__ == '__main__':
    print(u"Main Cache")
    running = True
    cacheData = WorkerCache()
    cacheData.start()
    while running :
        time.sleep(0.05)
    print(u"**************** Finished cache *******************")

