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

@author: Maxence Dunnewind <maxence@dunnewind.net>
@copyright: (C) 2007-2013 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

from domogik.common.scenario.actions.abstract import AbstractAction


class LogAction(AbstractAction):
    """ Simple action that log something in scenario logfile
    """

    def __init__(self, log=None):
        AbstractAction.__init__(self, log)
        self.set_description("Simply put some string in log file.")

    def do_action(self, condition, tests):
        self._log.info("{0}".format(self._params['message']))

    def get_expected_entries(self):
        return {'message': {'type': 'string',
                            'description': 'some extra message to put in log',
                            'default': ''}
               }
