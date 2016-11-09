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
@copyright: (C) 2007-2016 Domogik project
@license: GPL(v3)
@organization: Domogik
"""
from __future__ import absolute_import, division, print_function, unicode_literals
from domogik.scenario.actions.abstract import AbstractAction


class PassAction(AbstractAction):
    """ Simple action that does absolutly nothing
    """

    def __init__(self, log=None, params=None):
        AbstractAction.__init__(self, log)
        self.set_description("Do nothing.")

    def do_action(self):
        self._log.info("Doing nothing :)")

    def get_expected_entries(self):
        return {}
