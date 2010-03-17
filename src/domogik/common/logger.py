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

Manage logs

Implements
==========

- Logger.__init__(self, plugin_name = None)
- Logger.__getattr__(self, attr)
- Logger.__setattr__(self, attr, value)
- Logger.__init__(self, plugin_name)
- Logger.get_logger(self)

@author: Maxence Dunnewind <maxence@dunnewind.net>
@copyright: (C) 2007-2009 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

import logging
from domogik.common.configloader import Loader


class Logger():
    '''
    Logger for the xPL system.
    Define main config parameters to help scripts to use logging facilities
    with a minimum of config
    '''

    def __init__(self, plugin_name):
        '''
        Get a logger with provided parameters and set config
        @param file : the file to record logs into with the path
        @param level : min level of the message to record, can be one of
        'debug', 'info', 'warning', 'error', 'critical'
        '''
        LEVELS = {'debug': logging.DEBUG,
              'info': logging.INFO,
              'warning': logging.WARNING,
              'error': logging.ERROR,
              'critical': logging.CRITICAL}

        cfg = Loader()
        config = cfg.load()[0]
        file = "%s/%s.log" % (config['log_dir_path'], plugin_name)
        level = config['log_level']

        if level not in LEVELS:
            raise ValueError("level must be one of 'debug','info','warning',"\
                    "'error','critical'. Check your config.")

        logger = logging.getLogger('domogik-%s' % plugin_name)
        hdlr = logging.FileHandler(file)
        formatter = logging.Formatter('%(asctime)s %(name)s %(levelname)s %(message)s')
        hdlr.setFormatter(formatter)
        logger.addHandler(hdlr)
        logger.setLevel(LEVELS[level])

        self.logger = logger

    def get_logger(self):
        '''
        returns the configured logger instance
        '''
        return self.logger
