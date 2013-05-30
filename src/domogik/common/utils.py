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

Miscellaneous utility functions

Implements
==========


@author: Marc SCHNEIDER <marc@mirelsol.org>
@copyright: (C) 2007-2012 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

from socket import gethostname
from exceptions import ImportError, AttributeError

def get_sanitized_hostname():
    """ Get the sanitized hostname of the host 
    This will lower it and keep only the part before the first dot
    """
    return gethostname().lower().split('.')[0].replace('-','')[0:16]

def ucode(my_string):
    """Convert a string into unicode or return None if None value is passed

    @param my_string : string value to convert
    @return a unicode string

    """
    if my_string is not None:
        if not type(my_string) == str:
            return str(my_string).decode("utf-8")
        else:
            return my_string.decode("utf-8")
    else:
        return None

def call_package_conversion(log, plugin, method, value):
    """Load the correct module, and encode the value

    @param log: an instalce of a Logger
    @param plugin: the plugin (package) name
    @param method: what methode to load from the conversion class
    @param value: the value to convert
    @return the converted value or None on error
 
    """
    modulename = 'domogik_packages.conversions.{0}'.format(plugin)
    classname = '{0}Conversions'.format(plugin)
    try:
        module = __import__(modulename, fromlist=[classname])
    except ImportError as err:
        log.critical("Can not import module {0}: {1}".format(modulename, err))
        return value
    try:
        staticclass = getattr(module, classname)
        staticmethode = getattr(staticclass, method)
    except AttributeError as err:
        log.critical("Can not load class ({0}) or methode ({1}): {2}".format(classname, method, err))
        return value
    return staticmethode(value)

