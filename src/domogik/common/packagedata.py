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

Insert plugin data in database

Implements
==========

PluginData

@author: Fritz <fritz.smh@gmail.com>
@copyright: (C) 2007-2012 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

from domogik.common.packagejson import PackageJson, PackageException
from domogik.common.database import DbHelper
import sys
import traceback

class PackageData():
    """ Tool to insert necessary data in database
    """

    def __init__(self, json_path):
        """ Init tool
            @param plugin_name : plugin name
        """

        self._db = DbHelper()
        try:
            self.pkg = PackageJson(path = json_path).json
        except:
            print(str(traceback.format_exc()))
            return
        print("Json file OK")

        # check type == plugin
        if self.pkg["identity"]["type"] not in ["plugin", "external"]:
            print("Error : this package type is not recognized")
            exit()
        # check if json version is at least 2
        if self.pkg['json_version'] < 2:
            print("Error : this package is to old for this version of domogik")
            exit()

    def insert(self):
        """ Insert data for plugin
        """
        ### Technology
        print("Technology %s" % self.pkg["technology"]["id"])
        if self._db.get_device_technology_by_id(self.pkg["technology"]["id"]) == None:
            # add if not exists
            print("add...")
            self._db.add_device_technology(self.pkg["technology"]["id"],
                                           self.pkg["technology"]["name"],
                                           self.pkg["technology"]["description"])
        else:
            # update if exists
            print("update...")
            self._db.update_device_technology(self.pkg["technology"]["id"],
                                           self.pkg["technology"]["name"],
                                           self.pkg["technology"]["description"])
 
        ### Device types
        for device_type in self.pkg["device_types"].keys():
            print("Device type %s" % device_type)
            device_type = self.pkg["device_types"][device_type]
            if self._db.get_device_type_by_id(device_type["id"]) == None:
                # add if not exists
                print("add...")
                self._db.add_device_type(device_type["id"],
                                         device_type["name"],
                                         self.pkg["technology"]["id"],
                                         device_type["description"])
            else:
                # update if exists
                print("update...")
                self._db.update_device_type(device_type["id"],
                                         device_type["name"],
                                         self.pkg["technology"]["id"],
                                         device_type["description"])
