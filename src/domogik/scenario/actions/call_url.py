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
from domogik.common.utils import ucode
import traceback
try:
    # python3
    from urllib.request import urlopen
    from urllib.parse import quote, urlparse
except ImportError:
    # python2
    from urllib import urlopen, quote
    from urlparse import parse_qs, urlparse


class CallUrlAction(AbstractAction):
    """ Simple action that call an url
    """

    def __init__(self, log=None, params=None):
        AbstractAction.__init__(self, log)
        self.set_description("Call an url.")

    def do_action(self):
        url = self._params['url']

        self._log.info(u"Calling url : {0}".format(url))
        try:
            # encode url
            url = url.encode('utf-8')
            url_elts = urlparse(url)
            url_args = url_elts.query.split("&")
            new_url_args = u""
            for arg in url_args:
                if arg != '':
                    key, value = arg.split("=")
                    new_url_args += u"{0}={1}&".format(quote(key), quote(value))
            new_url = u"{0}://{1}{2}?{3}".format(url_elts.scheme,
                                               url_elts.netloc,
                                               url_elts.path,
                                               new_url_args)
            if new_url.endswith('?'):
                new_url = new_url[:-1]
            # call url
            self._log.debug(u"Calling url (transformed) : {0}".format(new_url))
            html = urlopen(new_url)
            self._log.info(u"Call url OK")
        except:
            self._log.warning(u"Error when calling url from action.CallUrlAction : {0}".format(traceback.format_exc()))
           
    def get_expected_entries(self):
        return {'url': {'type': 'string',
                        'description': 'Url',
                        'default': 'http://'}
               }
