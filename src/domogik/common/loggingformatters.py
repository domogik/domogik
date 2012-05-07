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

Provide some formatters for the logging services.

Implements
==========

- DefaultFormatter
- ColorFormatter
- SpaceFormatter
- SpaceColorFormatter

@author:Frédéric Mantegazza <frederic.mantegazza@gbiloba.org>
@author: Maxence Dunnewind <maxence@dunnewind.net>
@copyright: (C) 2007-2012 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

import logging
import time
import sys


class DefaultFormatter(logging.Formatter):
    """ Default formatter for subscribers.
    """


class ColorFormatter(DefaultFormatter):
    """ Formatter with colors.

    The color depends on the level of the log.
    We only use colors on linux/MacOS plateformes.
    """
    if sys.platform in ('linux2', 'darwin'):
        colors = {'trace': "\033[0;36;40;22m",     # cyan on black, normal
                  'debug': "\033[0;36;40;1m",      # cyan on black, bold
                  'info': "\033[0;37;40;1m",       # white on black, bold
                  'warning': "\033[0;33;40;1m",    # brown on black, bold
                  'error': "\033[0;31;40;1m",      # red on black, bold
                  'critical': "\033[0;37;41;1m",   # white on red, bold
                  'default': "\033[0m",            # default
                  }
    else:
        colors = {'trace': "",
                  'debug': "",
                  'info': "",
                  'warning': "",
                  'error': "",
                  'critical': "",
                  'default': "",
                  }

    def _to_color(self, msg, level_name):
        """ Colorize according to log level.
        """
        if level_name == 'TRACE':
            color = ColorFormatter.colors['trace']
        elif level_name == 'DEBUG':
            color = ColorFormatter.colors['debug']
        elif  level_name in 'INFO':
            color = ColorFormatter.colors['info']
        elif level_name == 'WARNING':
            color = ColorFormatter.colors['warning']
        elif level_name == 'ERROR':
            color = ColorFormatter.colors['error']
        elif level_name == 'CRITICAL':
            color = ColorFormatter.colors['critical']
        else:
            color = ColorFormatter.colors['default']

        return color + msg + ColorFormatter.colors['default']

    def format(self, record):
        msg = DefaultFormatter.format(self, record)
        return self._to_color(msg, record.levelname)


class SpaceFormatter(DefaultFormatter):
    """ Formatter with empty lines.
    """
    _last_log_time = time.time()

    def _add_space(self, msg):
        """ Add empty lines.

        The number of empty lines depends on the time since
        the last record has been sent.
        """
        if time.time() - SpaceFormatter._last_log_time > 3600:
            space = "\n\n\n"
        elif time.time() - self._last_log_time > 60:
            space = "\n\n"
        elif time.time() - self._last_log_time > 1:
            space = "\n"
        else:
            space = ""
        SpaceFormatter._last_log_time = time.time()

        return space + msg

    def format(self, record):
        msg = DefaultFormatter.format(self, record)
        return self._add_space(msg)


class SpaceColorFormatter(SpaceFormatter, ColorFormatter):
    """ Formatter with colors *and* empty lines.
    """
    def format(self, record):
        msg = SpaceFormatter.format(self, record)
        return self._to_color(msg, record.levelname)
