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
        for device_type in self.pkg["device_types"]:
            print("Device type %s" % device_type["id"])
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
 
        ### Device feature model
        for device_feature_model in self.pkg["device_feature_models"]:
            print("Device feature model %s" % device_feature_model["id"])
            if self._db.get_device_feature_model_by_id(device_feature_model["id"]) == None:
                # add if not exists
                print("add...")
                if device_feature_model["feature_type"] == "sensor":
                    self._db.add_sensor_feature_model(sf_id = device_feature_model["id"],
                                                      sf_name = device_feature_model["name"],
                                                      sf_device_type_id = device_feature_model["device_type_id"],
                                                      sf_value_type = device_feature_model["value_type"],
                                                      sf_unit= device_feature_model["unit"])
                elif device_feature_model["feature_type"] == "actuator":
                    self._db.add_actuator_feature_model(af_id = device_feature_model["id"],
                                                        af_name = device_feature_model["name"],
                                                        af_device_type_id = device_feature_model["device_type_id"],
                                                        af_value_type = device_feature_model["value_type"],
                                                        af_xpl_command = device_feature_model["xpl_command"],
                                                        af_value_field = device_feature_model["value_field"],
                                                        af_values = device_feature_model["values"],
                                                        af_stat_key = af_device_feature_model["stat_key"])
            else:
                # update if exists
                print("update...")
                if device_feature_model["feature_type"] == "sensor":
                    self._db.update_sensor_feature_model(sf_id = device_feature_model["id"],
                                                      sf_name = device_feature_model["name"],
                                                      sf_value_type = device_feature_model["value_type"],
                                                      sf_stat_key = device_feature_model["stat_key"],
                                                      sf_unit= device_feature_model["unit"])
                elif device_feature_model["feature_type"] == "actuator":
                    self._db.update_actuator_feature_model(af_id = device_feature_model["id"],
                                                        af_name = device_feature_model["name"],
                                                        af_value_type = device_feature_model["value_type"],
                                                        af_xpl_command = device_feature_model["xpl_command"],
                                                        af_value_field = device_feature_model["value_field"],
                                                        af_values = device_feature_model["values"],
                                                        af_stat_key = device_feature_model["stat_key"])
        
        
       

