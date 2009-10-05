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

Provide configuration management classes.

Implements
==========

- ConfigManager

@author:Frédéric Mantegazza <frederic.mantegazza@gbiloba.org>
@author: Maxence Dunnewind <maxence@dunnewind.net>
@copyright: (C) 2008-2009 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

import os
import os.path
import ConfigParser

CONFIG_FILENAME = "domogik.conf"


class ConfigManager(object):
    """ Config manager object.

    @ivar __config: low-level config object
    @itype __config: SafeConfigParser

    @ivar __config_filename: name of the config file
    @itype __config_filename: str
    """
    __state = {}
    __init = True

    def __new__(cls, *args, **kwds):
        self = object.__new__(cls, *args, **kwds)
        self.__dict__ = cls.__state
        return self

    def __init__(self, module_name=None):
        """ Init the config manager.

        @param module_name: name of the module which loads the configuration
        @type module_name: str

        @raise ValueError: bad usage or no configuration found
        """
        super(ConfigManager, self).__init__()
        if ConfigManager.__init:
            if module_name is None:
                raise ValueError("Module name is mandatory in the first call")

            # Create user config dir if needed
            user_config_dir = os.path.join(os.path.expanduser("~"), ".config", "domogik")
            if not os.path.exists(user_config_dir):
                os.path.makedirs(user_config_dir)

            # Create low-level config object
            self.__config = ConfigParser.SafeConfigParser()
            self.__config_file = None

            ConfigManager.__init = False

    def load(self):
        """ Load configuration from file.
        """
        config_files = []
        user_config_dir = os.path.join(os.path.expanduser("~"), ".config", "domogik")
        config_files.append(os.path.join(user_config_dir, CONFIG_FILENAME))
        config_files.append(os.path.join("/usr/local/etc", CONFIG_FILENAME))
        config_files.append(os.path.join("/etc", CONFIG_FILENAME))
        for config_file in config_files:
            if self.__config.read(config_file):
                break
        else:
            raise ValueError("No configuration found")
        self.__config_filename = config_file

    def save(self):
        """ Save back configuration to file.

        Config is saved in the user config directory.
        """
        file_ = file(self.__config_filename, 'w')
        self.__config.write(file_)

    def get(self, section, option):
        """ Get a string value.

        @param section: section name to use
        @type section: str

        @param option: option to get value from
        @type option: str
        """
        return self.__config.get(section, option)

    def get_int(self, section, option):
        """ Get an integer value.

        @param section: section name to use
        @type section: str

        @param option: option to get value from
        @type option: int
        """
        return self.__config.getint(section, option)

    def get_float(self, section, option):
        """ Get a float value.

        @param section: section name to use
        @type section: str

        @param option: option to get value from
        @type option: float
        """
        return self.__config.getfloat(section, option)

    def get_bool(self, section, option):
        """ Get a boolean value.

        @param section: section name to use
        @type section: str

        @param option: option to get value from
        @type option: bool
        """
        return self.__config.getboolean(section, option)

    def set(self, section, option, value):
        """ Set a string value.

        @param section: section name to use
        @type section: str

        @param option: option to set value to
        @type option: str

        @param value: value to set
        @type value: str
        """
        value = value.replace("%", "%%")
        self.__config.set(section, option, value)

    def set_int(self, section, option, value):
        """ Set an integer value.

        @param section: section name to use
        @type section: str

        @param option: option to set value to
        @type option: str

        @param value: value to set
        @type value: int
        """
        self.__config.set(section, option, "%d" % value)

    def set_float(self, section, option, value, decimals=3):
        """ Set a float value.

        @param section: section name to use
        @type section: str

        @param option: option to set value to
        @type option: str

        @param value: value to set
        @type value: float

        @param decimals: number of decimals
        @type decimals: int
        """
        self.__config.set(section, option, ("%(format)s" % {'format': "%%.%df" % decimals}) % value)

    def set_bool(self, section, option, value):
        """ Set a boolean value.

        @param section: section name to use
        @type section: str

        @param option: option to set value to
        @type option: str

        @param value: value to set
        @type value: str
        """
        self.__config.set(section, option, str(value))
