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

@author: Fritz SMH <fritz.smh@gmail.com>
@copyright: (C) 2007-2015 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

from domogik.scenario.actions.abstract import AbstractAction
import time


class PauseAction(AbstractAction):
    """ Do a pause between 2 actions
    """

    def __init__(self, log=None, params=None):
        AbstractAction.__init__(self, log)
        self.set_description("Do a pause.")

    def do_action(self):
        delay = self._params['delay']

        self._log.info("Do a pause of {0} seconds".format(delay))
        try:
            time.sleep(int(delay))
        except:
            self._log.error("Error while casting delay '{0}' to int value".format(delay))

    def get_expected_entries(self):
        return {'delay': {'type': 'integer',
                            'description': 'Delay in seconds',
                            'default': '5'}
               }
