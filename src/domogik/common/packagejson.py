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

Library to simply manager packages's json file description

Implements
==========

PackageJson

@author: Fritz <fritz.smh@gmail.com>
@copyright: (C) 2007-2010 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

from domogik.common.configloader import Loader
import traceback
import datetime
import json
try:
    # python3
    from urllib.request import urlopen
except ImportError:
    # python2
    from urllib import urlopen

#TODO : why this import fails ?
#from domogik.xpl.common.plugin import PACKAGES_DIR
PACKAGES_DIR = "domogik_packages"





class PackageException(Exception):
    """
    Package exception
    """

    def __init__(self, value):
        Exception.__init__(self)
        self.value = value

    def __str__(self):
        return repr(self.value)


class PackageJson():
    """ PackageJson class
        load the file into a json and complete it
    """
    def __init__(self, name = None, url = None, path = None, pkg_type = "plugin", data = None):
        """ Read json file of a plugin and make an object from it
            @param name : name of package
            @param url : url of file
            @param path : path of file
            @param pkg_type : package type (default : 'plugin')
                          To use only with name != None
            @param data : json data as a python object. Used by package.py when installing a zip file : the json is read from memory
        """
        json_file = None
        try:
            # load from sources repository
            if name != None:
                # get config
                cfg = Loader('domogik')
                config = cfg.load()
                conf = dict(config[1])

                if pkg_type in ["plugin", "brain", "interface"]:
                    json_file = "{0}/{1}/{2}_{3}/info.json".format(conf['libraries_path'], PACKAGES_DIR, pkg_type, name)
                    icon_file = "{0}/{1}/{2}_{3}/design/icon.png".format(conf['libraries_path'], PACKAGES_DIR, pkg_type, name)
                else:
                    raise PackageException("Type '{0}' doesn't exists".format(pkg_type))
                #json_file = "%s/%s.json" % (json_directory, name)

                self.json = json.load(open(json_file))

            elif path != None:
                json_file = path
                icon_file = None
                self.json = json.load(open(json_file))

            elif url != None:
                json_file = url
                icon_file = None
                json_data = urlopen(json_file)
                # TODO : there is an error here!!!!!
                self.json = json.load(xml_data)

            elif data != None:
                json_file = None
                icon_file = None
                self.json = data

            self.validate()

            ### complete json
            # identity data
            self.json["identity"]["package_id"] = "{0}-{1}".format(self.json["identity"]["type"],
                                                           self.json["identity"]["name"])
            self.json["identity"]["icon_file"] = icon_file

            if not self.json["identity"].has_key("xpl_clients_only"):
                self.json["identity"]["xpl_clients_only"] = False

            if not self.json["identity"].has_key("compliant_xpl_clients"):
                self.json["identity"]["compliant_xpl_clients"] = []

            # common configuration items
            # to add only for a plugin with identity>xpl_clients_only not set to True !
            if self.json["identity"]["type"] in ["plugin", "interface"] and not (self.json["identity"].has_key("xpl_clients_only") and self.json["identity"]["xpl_clients_only"] == True):
                auto_startup = {
                                   "default": False,
                                   "description": "Automatically start the client at Domogik startup",
                                   "key": "auto_startup",
                                   "name" : "Start the client with Domogik",
                                   "required": True,
                                   "type": "boolean"
                               }
                # check that auto_startup key is not already defined in the json
                for config_elt in self.json["configuration"]:
                    if config_elt["key"] == "auto_startup":
                        raise PackageException("Configuration parameter 'auto_startup' has not to be defined in the json file. Please remove it")
                self.json["configuration"].insert(0, auto_startup)
                  


        except PackageException as exp:
            raise PackageException(exp.value)
        except:
            raise PackageException("Error reading json file : {0} : {1}".format(json_file, str(traceback.format_exc())))


    #def cache_xml(self, cache_folder, url, repo_url, priority):
    #    """ Add package url info in xml data
    #        Store xml in a file in cache_folder
    #        @param cache_folder : folder to put xml file
    #        @param url : package url
    #        @param repo_url : repository url
    #        @param priority : repository priority
    #    """
    #    top_elt = self.xml_content.documentElement
    #    new_elt = self.xml_content.createElementNS(None, 'repository')
    #    new_elt.setAttribute("package", url)
    #    new_elt.setAttribute("priority", priority)
    #    new_elt.setAttribute("source", repo_url)
    #    top_elt.appendChild(new_elt)
    #    cache_file = open("%s/%s" % (cache_folder, self.json_filename), "w") 
    #    cache_file.write(self.xml_content.toxml().encode("utf-8"))
    #    cache_file.close()

    #def set_repo_source(self, source):
    #    """ Add source info in xml data
    #        Store in xml the repository from which it comes
    #        @param source : repository url
    #    """
    #    top_elt = self.xml_content.documentElement
    #    new_elt = self.xml_content.createElementNS(None, 'repository')
    #    new_elt.setAttribute("source", source)
    #    top_elt.appendChild(new_elt)
    #    my_file = open("%s" % (self.info_file), "w") 
    #    my_file.write(self.xml_content.toxml().encode("utf-8"))
    #    my_file.close()

    def validate(self):
        if self.json["json_version"] == 2:
            self._validate_02()
        else:
            return False

    def _validate_keys(self, expected, name, lst, optional=[]):
        for exp in expected:
            if exp not in lst:
                raise PackageException("key '{0}' not found in {1}".format(exp, name))
        explst = expected + optional
        for item in lst:
            if item not in explst:
                raise PackageException("unknown key '{0}' found in {1}".format(item, name))

    def _validate_02(self):
        fieldTypes = ["boolean", "string", "choice", "date", "time", "datetime", "float", "integer", "email", "ipv4", "ipv6", "url", "password"]
        try:
            #check that all main keys are in the file
            expected = ["configuration", "xpl_commands", "xpl_stats", "commands", "sensors", "device_types", "identity", "json_version"]
            self._validate_keys(expected, "file", self.json.keys(), ["products", "external"])

            # validate identity
            expected = ["author", "author_email", "description", "domogik_min_version", "name", "type", "version"]
            optional = ["tags", "dependencies", "package_id", "icon_file", "xpl_clients_only", "compliant_xpl_clients"]
            if type(self.json["identity"]) != dict:
                raise PackageException("Identity part is NOT a dictionary!")
            self._validate_keys(expected, "an identity param", self.json["identity"].keys(), optional)

            # validate configuration
            expected = ["default", "description", "key", "name", "required", "type"]
            optional = ["sort", "max_value", "min_value", "choices", "mask", "multiline"]
            if type(self.json["configuration"]) != list:
                raise PackageException("Configuration part is NOT a list!")
            for conf in self.json["configuration"]:
                self._validate_keys(expected, "a configuration item param", conf.keys(), optional)
                if conf['type'] not in fieldTypes:
                    raise PackageException("Type ({0}) in a config item is not in the allowd list: {1}".format(conf['type'], fieldTypes))

            # validate products
            if 'products' in self.json.keys():
                expected = ["name", "id", "documentation", "type"]
                for prod in self.json['products']:
                    self._validate_keys(expected, "a product", prod.keys())

            #validate the device_type
            if type(self.json["device_types"]) != dict:
                raise PackageException("Device_types part is NOT a dictionary!")
            for devtype in self.json["device_types"]:
                devt = self.json["device_types"][devtype]
                expected = ['id', 'name', 'description', 'commands', 'sensors', 'parameters']
                self._validate_keys(expected, "device_type {0}".format(devtype), devt.keys())
                #check that all commands exists inisde each device_type
                if type(devt["commands"]) != list:
                    raise PackageException("Commands list for device_type {0} is NOT a list!".format(devtype))
                for cmd in devt["commands"]:
                    if cmd not in self.json["commands"].keys():    
                        raise PackageException("cmd {0} defined in device_type {1} is not found".format(cmd, devtype))
                #check that all sensors exists inside each device type
                if type(devt["sensors"]) != list:
                    raise PackageException("Sensors list for device_type {0} is NOT a list!".format(devtype))
                for sens in devt["sensors"]:
                    if sens not in self.json["sensors"].keys():    
                        raise PackageException("sensor {0} defined in device_type {1} is not found".format(sens, devtype))
                #see that each xplparam inside device_type has the following keys: key, description, type
                expected = ["key", "type", "description", "xpl"]
                optional = ["max_value", "min_value", "choices", "mask", "multiline", "default"]
                if type(devt["parameters"]) != list:
                    raise PackageException("Parameters list for device_type {0} is NOT a list!".format(devtype))
                for par in devt["parameters"]:
                    self._validate_keys(expected, "a param for device_type {0}".format(devtype), par.keys(), optional)
                    if par['type'] not in fieldTypes:
                        raise PackageException("Type ({0}) in a config item is not in the allowd list: {1}".format(par['type'], fieldTypes))

            #validate the commands
            if type(self.json["commands"]) != dict:
                raise PackageException("Commands part is NOT a dictionary!")
            for cmdid in self.json["commands"]:
                cmd = self.json["commands"][cmdid]
                expected = ['name', 'return_confirmation', 'parameters']
                optional = ['xpl_command']
                self._validate_keys(expected, "command {0}".format(cmdid), cmd.keys(), optional)
                # validate the params
                expected = ['key', 'data_type', 'conversion']
                if type(cmd['parameters']) != list:
                    raise PackageException("Parameters for command {0} is not a list".format(cmdid))
                for par in cmd['parameters']:
                    self._validate_keys(expected, "a param for command {0}".format(cmdid), par.keys())
                # see that the xpl_command is defined
                if "xpl_command" in cmd and cmd["xpl_command"] not in self.json["xpl_commands"].keys():
                    raise PackageException("xpl_command {0} defined in command {1} is not found".format(cmd["xpl_command"], cmdid))

            #validate the sensors
            if type(self.json["sensors"]) != dict:
                raise PackageException("Sensor part is NOT a dictionary!")
            for senid in self.json["sensors"]:
                sens = self.json["sensors"][senid]
                expected = ['name', 'data_type', 'conversion', 'history', 'incremental', 'timeout']
                hexpected = ['store', 'max', 'expire', 'round_value', 'duplicate']
                self._validate_keys(expected, "sensor {0}".format(senid), list(sens.keys()))
                self._validate_keys(hexpected, "sensor {0} history".format(senid), list(sens['history'].keys()))

            #validate the xpl command
            if type(self.json["xpl_commands"]) != dict:
                raise PackageException("Xpl_commands part is NOT a dictionary!")
            for xcmdid in self.json["xpl_commands"]:
                xcmd = self.json["xpl_commands"][xcmdid]
                expected = ["name", "schema", "xplstat_name", "parameters"]
                self._validate_keys(expected, "xpl_command {0}".format(xcmdid), xcmd.keys())
                # parameters
                expected = ["static", "device"]
                self._validate_keys(expected, "parameters for xpl_command {0}".format(xcmdid), xcmd['parameters'].keys())
                # static parameter
                expected = ["key", "value"]
                if type(xcmd['parameters']['static']) != list:
                    raise PackageException("Static parameters for xpl_command {0} is not a list".format(xcmdid))
                for stat in xcmd['parameters']['static']:
                    self._validate_keys(expected, "a static parameter for xpl_command {0}".format(xcmdid), stat.keys())
                # device parameter
                expected = ["key", "description", "type"]
                optional = ["default"]
                if type(xcmd['parameters']['device']) != list:
                    raise PackageException("Device parameters for xpl_command {0} is not a list".format(xcmdid))
                for stat in xcmd['parameters']['device']:
                    self._validate_keys(expected, "a device parameter for xpl_command {0}".format(xcmdid), stat.keys(), optional)
                    if stat['type'] not in fieldTypes:
                        raise PackageException("Type ({0}) in a config item is not in the allowd list: {1}".format(stat['type'], fieldTypes))
                # see that the xpl_stat is defined
                if xcmd["xplstat_name"] not in self.json["xpl_stats"].keys():
                    raise PackageException("xplstat_name {0} defined in xpl_command {1} is not found".format(xcmd["xplstat_name"], xcmdid))

            #validate the xpl stats
            if type(self.json["xpl_stats"]) != dict:
                raise PackageException("Xpl_stats part is NOT a dictionary!")
            for xstatid in self.json["xpl_stats"]:
                xstat = self.json["xpl_stats"][xstatid]
                expected = ["name", "schema", "parameters"]
                self._validate_keys(expected, "xpl_command {0}".format(xstatid), xstat.keys())
                # parameters
                expected = ["static", "device", "dynamic"]
                self._validate_keys(expected, "parameters for xpl_stat {0}".format(xstatid), xstat['parameters'].keys())
                # static parameter
                expected = ["key", "value"]
                if type(xstat['parameters']['static']) != list:
                    raise PackageException("Static parameters for xpl_stat {0} is not a list".format(xstatid))
                for stat in xstat['parameters']['static']:
                    self._validate_keys(expected, "a static parameter for xpl_stat {0}".format(xstatid), stat.keys())
                # device parameter
                expected = ["key", "description", "type"]
                optional = ["default", "multiple"]
                if type(xstat['parameters']['device']) != list:
                    raise PackageException("Device parameters for xpl_stat {0} is not a list".format(xstatid))
                for stat in xstat['parameters']['device']:
                    self._validate_keys(expected, "a device parameter for xpl_stat {0}".format(xstatid), stat.keys(), optional)
                    if stat['type'] not in fieldTypes:
                        raise PackageException("Type ({0}) in a config item is not in the allowd list: {1}".format(stat['type'], fieldTypes))
                # dynamic parameter
                expected = ["key", "sensor"]
                opt = ["ignore_values"]
                if type(xstat['parameters']['dynamic']) != list:
                    raise PackageException("Dynamic parameters for xpl_stat {0} is not a list".format(xstatid))
                for stat in xstat['parameters']['dynamic']:
                    self._validate_keys(expected, "a dynamic parameter for xpl_stat {0}".format(xstatid), stat.keys(), opt)
                    # check that the sensor exists
                    if stat['sensor'] not in self.json["sensors"].keys():    
                        raise PackageException("sensor {0} defined in xpl_stat {1} is not found".format(stat['sensor'], xstatid))
        except PackageException as exp:
            raise PackageException("Error validating the json: {0}".format(exp.value))

    def set_generated(self, path):
        """ Add generation date info in json data
            @param path : path to json file
        """
        my_json = json.load(open(path))
        my_json["identity"]["generated"] = str(datetime.datetime.now())
        my_file = open(path, "w")
        my_file.write(json.dumps(my_json))
        my_file.close()

    def get_json(self):
        """ Return the json data
        """
        return self.json

    def display(self):
        """ Display xml data in a fine way
        """
        print(u"---- Package informations -------------------------------")
        print(u"Type                : {0}".format(self.json["identity"]["type"]))
        print(u"Name                : {0}".format(self.json["identity"]["name"]))
        print(u"Package id          : {0}".format(self.json["identity"]["package_id"]))
        print(u"Version             : {0}".format(self.json["identity"]["version"]))
        print(u"Tags                : {0}".format(self.json["identity"]["tags"]))
        print(u"Link for doc        : {0}".format(self.json["identity"]["documentation"]))
        print(u"Description         : {0}".format(self.json["identity"]["description"]))
        print(u"Changelog           : {0}".format(self.json["identity"]["changelog"]))
        print(u"Author              : {0}".format(self.json["identity"]["author"]))
        print(u"Author's email      : {0}".format(self.json["identity"]["author_email"]))
        print(u"Domogik min version : {0}".format(self.json["identity"]["domogik_min_version"]))
        print(u"---------------------------------------------------------")

    def find_xplstats_for_device_type(self, devtype):
        if self.json["json_version"] != 2:
            return "Bad json version for the plugin"
        ret = {}
        # loop over all xplstat params and see if the sensor is linked to the above list
        for xstatid in self.json["xpl_stats"]:
            xstat = self.json["xpl_stats"][xstatid]
            for stat in xstat['parameters']['dynamic']:
                if stat['sensor'] in self.json["device_types"][devtype]['sensors']:
                    if stat['sensor'] not in ret:
                        ret[stat['sensor']] = []
                    ret[stat['sensor']].append( xstatid )
                        
        return ret


def set_nightly_version(path):
    """ update version for the nightly build
        @param path : path to json file
    """
    my_json = json.load(open(path))
    # suffix the version with .devYYYYMMDD
    suffix = ".dev{0}".format(datetime.datetime.now().strftime('%Y%m%d'))
    my_json["identity"]["version"] += suffix
    my_file = open(path, "w")
    my_file.write(json.dumps(my_json))
    my_file.close()

if __name__ == "__main__":
    pjson = PackageJson("plcbus")
    pjson = PackageJson("velbus")
