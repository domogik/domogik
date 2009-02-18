#!/usr/bin/python
# -*- encoding:utf-8 -*-

# Copyright 2008 Domogik project

# This file is part of Domogik.
# Domogik is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# Domogik is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with Domogik.  If not, see <http://www.gnu.org/licenses/>.

# Author: Maxence Dunnewind <maxence@dunnewind.net>

# $LastChangedBy: maxence $
# $LastChangedDate: 2009-02-03 16:58:56 +0100 (mar 03 fév 2009) $
# $LastChangedRevision: 326 $

import logging
from configloader import Loader

class Logger():
    '''
    Logger for the xPL system. 
    Define main config parameters to help scripts to use logging facilities with a minimum of config
    '''

    def __init__(self, module_name = 'domogik'):
        '''
        Get a logger with provided parameters and set config
        @param file : the file to record logs into with the path
        @param level : min level of the message to record, can be one of 'debug','info','warning','error','critical'
        '''
        LEVELS = {'debug': logging.DEBUG,
              'info': logging.INFO,
              'warning': logging.WARNING,
              'error': logging.ERROR,
              'critical': logging.CRITICAL}

        cfg = Loader()
        config = cfg.load()[0]
        file = "%s/%s.log" % (config['log_dir_path'], module_name)
        level = config['log_level']

        if not LEVELS.has_key(level):
            raise ValueError, "level must be one of  'debug','info','warning','error','critical'. Check your config."

        logger = logging.getLogger('domogik-%s' % module_name)
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
