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

Manage logs

Implements
==========

- Logger.__init__(self, component_name = None)
- Logger.__getattr__(self, attr)
- Logger.__setattr__(self, attr, value)
- Logger.__init__(self, component_name)
- Logger.get_logger(self)

@author: Maxence Dunnewind <maxence@dunnewind.net>
@copyright: (C) 2007-2012 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

import logging
from logging.handlers import TimedRotatingFileHandler
import sys
from domogik.common.configloader import Loader

class Logger():
    '''
    Logger for Domogik
    Define main config parameters to help scripts to use logging facilities
    with a minimum of config
    '''

    logger = {}

    def __init__(self, component_name, domogik_prefix=True, use_filename=None, log_on_stdout=True):
        '''
        Get a logger with provided parameters and set config
        @param component_name : component name to log
        @param domogik_prefix : if logger name should be prefixed by 'domogik-'
        @param use_filename : if set tells the logger to use this file name (otherwise takes 'component_name')
        @param log_on_stdout : if set to True, allow to display logs in both stdout and log file
        '''
        if component_name not in self.logger:
            LEVELS = {
                        'debug': logging.DEBUG,
                        'info': logging.INFO,
                        'warning': logging.WARNING,
                        'error': logging.ERROR,
                        'critical': logging.CRITICAL
            }

            cfg = Loader()
            config = cfg.load()[0]
            if use_filename is None:
                filename = "{0}/{1}.log".format(config['log_dir_path'], component_name)
            else:
                filename = "{0}/{1}.log".format(config['log_dir_path'], use_filename)
            level = config['log_level']

            if 'log_when' not in config:
                config['log_when'] = 'D'
            if 'log_interval' not in config:
                config['log_interval'] = 1
            if 'log_backup_count' not in config:
                config['log_backup_count'] = 10

            if level not in LEVELS:
                raise ValueError("level must be one of 'debug','info','warning',"\
                        "'error','critical'. Check your config.")

            if domogik_prefix:
                my_logger = logging.getLogger('domogik-{0}'.format(component_name))
            else:
                my_logger = logging.getLogger(component_name)
            # log to file
            my_logger.propagate = 0
            if not my_logger.handlers:
                hdlr = TimedRotatingFileHandler(filename, \
                        when=config['log_when'], interval=int(config['log_interval']), \
                        backupCount=int(config['log_backup_count']))
                formatter = logging.Formatter('%(asctime)s %(name)s %(levelname)s %(message)s')
                hdlr.setFormatter(formatter)
                my_logger.addHandler(hdlr)

	        # if loglevvel is set to debug (all log entries also go to stdout)
                if (log_on_stdout or level == 'debug') and component_name.find('sqlalchemy') == -1:
                    dhdlr = logging.StreamHandler(sys.stdout)
                    dhdlr.setFormatter(formatter)
                    my_logger.addHandler(dhdlr)

            my_logger.setLevel(LEVELS[level])
            self.logger[component_name] = my_logger

    def set_format_mode(self, mode):
        formatter = None
        if mode == "messageOnly":
            formatter = logging.Formatter('%(message)s')
        if formatter:
            for log in self.get_logger().handlers:
                if type(log) is logging.StreamHandler:
                    log.setFormatter(formatter)

    def get_logger(self, logger_name = None):
        '''
        returns the configured logger instance
        @param logger_name : The name of the logger you want to get.
        If not provided, return the logger if only one exists
        '''
        if logger_name is not None:
            return self.__class__.logger[logger_name]
        elif len(self.__class__.logger.keys()) == 1:
            return self.__class__.logger[list(self.__class__.logger)[0]]
        else:
            raise AttributeError("You must specify a loggger name")

    def get_fds(self, logger_names):
        openFiles = []
        for name in logger_names:
            logger = self.logger[name]
            for handler in logger.handlers:
                if hasattr(handler, 'stream') and \
                    hasattr(handler.stream, 'fileno'):
                    openFiles.append(handler.stream) 
        return openFiles
