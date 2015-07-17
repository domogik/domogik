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
@copyright: (C) 2007-2013 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

from domogik.scenario.actions.abstract import AbstractAction
import traceback
try:
    # python3
    from urllib.request import urlopen
except ImportError:
    # python2
    from urllib import urlopen


class CallUrlAction(AbstractAction):
    """ Simple action that call an url
    """

    def __init__(self, log=None, params=None):
        AbstractAction.__init__(self, log)
        self.set_description("Call an url.")

    def do_action(self):
        self._log.info("Calling url : {0}".format(self._params['url']))
        try:
            html = urlopen(self._params['url'])
            self._log.info("Call url OK")
        except:
            self._log.warning("Error when calling url from action.CallUrlAction : {0}".format(traceback.format_exc()))
           
    def get_expected_entries(self):
        return {'url': {'type': 'string',
                        'description': 'Url',
                        'default': 'http://'}
               }
