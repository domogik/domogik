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

Provide some advanced logging services.

Implements
==========

- Logger

@author:Frédéric Mantegazza <frederic.mantegazza@gbiloba.org>
@author: Maxence Dunnewind <maxence@dunnewind.net>
@copyright: (C) 2008-2009 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

import logging
import logging.handlers
import StringIO
import traceback
import os.path

from domogik.common.configmanager import ConfigManager
from domogik.common.loggingformatters import ColorFormatter, SpaceFormatter, SpaceColorFormatter


class Logger(object):
    """ This is the real logger object.

    @ivar __logger_instance: low-level reference to the logger
    @itype __logger_instance: L{Logger<logging>}
    """
    __state = {}
    __init = True

    def __new__(cls, *args, **kwds):
        self = object.__new__(cls, *args, **kwds)
        self.__dict__ = cls.__state
        return self

    def __init__(self, name=None):
        """ Init the logger object.

        @param plugin_name: name of the plugin which uses this logger
        @type plugin_name: str

        @raise ValueError: bad usage
        """
        super(Logger, self).__init__()
        if Logger.__init:
            if name is None:
                raise ValueError("Logger name is mandatory in the first call")

            # Add the TRACE level
            logging.TRACE = logging.DEBUG - 5
            logging.addLevelName(logging.TRACE, "TRACE")

            # Get configuration
            config_manager = ConfigManager()
            config_manager.load()
            log_dir_path = config_manager.get('domogik', 'log_dir_path')
            log_file = "domogik-%s.log" % os.path.join(log_dir_path, name)
            log_level = config.get('logger', 'log_level')
            log_format = config.get('logger', 'log_format')
            log_file_max_size = config.get_int('logger', 'log_file_max_size')
            log_file_max_backup = config.get_int('logger', 'log_file_max_backup')

            # Formatters
            default_formatter = DefaultFormatter(log_format)
            space_formatter = SpaceFormatter(log_format)
            color_formatter = ColorFormatter(log_format)
            space_color_formatter = SpaceColorFormatter(log_format)

            # Create the logger instance
            logging.raiseExceptions = 0
            self.__logger_instance = logging.getLogger("domogik-%s" % name)
            self.set_level(log_level)

            # Add handlers
            # Console handler
            stdoutStreamHandler = logging.StreamHandler()
            stdoutStreamHandler.setFormatter(space_color_formatter)
            self.__logger_instance.addHandler(stdoutStreamHandler)

            # File handler
            fileHandler = logging.handlers.RotatingFileHandler(log_file, 'w',
                                                               log_file_max_size,
                                                               log_file_max_backup)
            fileHandler.setFormatter(default_formatter)
            self.__logger_instance.addHandler(fileHandler)

            Logger.__init = False

    def set_level(self, level):
        """ Change logger level.

        @param level: new level
        @type level: str

        @raise ValueError: the specified level does not exist
        """
        try:
            level_no = getattr(logging, level.upper())
        except AttributeError:
            raise ValueError("Unknown '%s' logger level" % level)
        else:
            self.__logger_instance.setLevel(level_no)

    def trace(self, message):
        """ Logs a message with level TRACE.

        @param message: message to log
        @type message: string
        """
        self.__logger_instance.log(logging.TRACE, message)

    def debug(self, message):
        """ Logs a message with level DEBUG.

        @param message: message to log
        @type message: string
        """
        self.__logger_instance.debug(message)

    def info(self, message):
        """ Logs a message with level INFO.

        @param message: message to log
        @type message: string
        """
        self.__logger_instance.info(message)

    def warning(self, message):
        """ Logs a message with level WARNING.

        @param message: message to log
        @type message: string
        """
        self.__logger_instance.warning(message)

    def error(self, message):
        """ Logs a message with level ERROR.

        @param message: message to log
        @type message: string
        """
        self.__logger_instance.error(message)

    def critical(self, message):
        """ Logs a message with level CRITICAL.

        @param message: message to log
        @type message: string
        """
        self.__logger_instance.critical(message)

    def exception(self, message, debug=False):
        """ Logs a message within exception traceback.

        The message uses the ERROR level, except if the debug flag
        is True; in this case, the message uses the DEBUG level.

        @param message: message to log
        @type message: string

        @param debug: flag to log exception on DEBUG level instead of EXCEPTION one
        @type debug: bool
        """
        if debug:
            self.debug(message, exc_info=True)
        else:
            self.__logger_instance.exception(message)

    def log(self, level, message):
        """ Logs a message with given level.

        @param level: log level to use
        @type level: int

        @param message: message to log
        @type message: string
        """
        self.__logger_instance.log(level, message)

    def getTraceback(self):
        """ Return the complete traceback.

        Should be called in an except statement.
        """
        tracebackString = StringIO.StringIO()
        traceback.print_exc(file=tracebackString)
        message = tracebackString.getvalue().strip()
        tracebackString.close()
        return message

    def shutdown(self):
        """ Shutdown the logging service.
        """
        logging.shutdown()
