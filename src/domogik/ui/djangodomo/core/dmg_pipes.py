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

Module purpose
==============

Overload django_pipes module to suit it to our needs
(request have the REST format eg /x/y/z instead of ?x&y&z

Implements
==========


@author: Domogik project
@copyright: (C) 2007-2009 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

import urllib2
from time import time
from django.core.cache import cache
from django.conf import settings
from django.utils import simplejson
import django_pipes as pipes
from django_pipes import debug_stats
from django_pipes.main import PipeBase
from django_pipes.main import PipeResultSet
from django_pipes.main import _log

from django_pipes.exceptions import ResourceNotAvailableException

if hasattr(settings, "PIPES_CACHE_EXPIRY"):
    default_cache_expiry = settings.PIPES_CACHE_EXPIRY
else:
    default_cache_expiry = 60

class DmgPipeManager(pipes.PipeManager):

    """
    Overload django_pipes.PipeManager.filter method
    (request parameters are formated using the REST syntax)
    @param params : a dictionnary with a single item named 'parameters'
    containing the REST parameters
    """
    def filter(self, params, should_cache=None, cache_expiry=None, retries=None):
        if hasattr(self.pipe, 'uri'):

            # should cache or not?
            if should_cache is None:
                # no per-request caching specified; lets look for cache option on the Pipe class
                if hasattr(self.pipe, 'should_cache'):
                    should_cache = self.pipe.should_cache
                else:
                    should_cache = True

            # how many retries?
            if retries is None:
                # no per-request retries configured; lets look for retries option on the Pipe class
                if hasattr(self.pipe, 'retries'):
                    retries = self.pipe.retries
                else:
                    retries = 0

            url_string = self.pipe.uri
            if len(params)>0:
                # Changed here :
                # url_string += "?%s" % urllib.urlencode(params)
                url_string += "/%s" % params['parameters']
            _log("Fetching: %s" % url_string)
            url_string = url_string.replace(" ",'')

            start = time()
            # Try the cache first
            resp = cache.get(url_string)
            if resp:
                # Yay! found in cache!
                _log("Found in cache.")
                stop = time()
                debug_stats.record_query(url_string, found_in_cache=True, time=stop-start)
            else:
                # Not found in cache
                _log("Not found in cache. Downloading...")

                attempts = 0
                while True:
                    try:
                        attempts += 1
                        respObj = urllib2.urlopen(url_string)
                        break
                    except urllib2.HTTPError, e:
                        stop = time()
                        debug_stats.record_query(url_string, failed=True, retries=attempts-1, time=stop-start)
                        raise ResourceNotAvailableException(code=e.code, resp=e.read())
                    except urllib2.URLError, e:
                        if attempts <= retries:
                            continue
                        else:
                            stop = time()
                            debug_stats.record_query(url_string, failed=True, retries=attempts-1, time=stop-start)
                            raise ResourceNotAvailableException(reason=e.reason)

                resp = respObj.read()
                if should_cache:
                    if cache_expiry is None:
                        if hasattr(self.pipe, 'cache_expiry'):
                            cache_expiry = self.pipe.cache_expiry
                        else:
                            cache_expiry = default_cache_expiry
                    cache.set(url_string, resp, cache_expiry)
                stop = time()
                debug_stats.record_query(url_string, retries=attempts-1, time=stop-start)

            resp_obj = simplejson.loads(resp)
            return PipeResultSet(self.pipe, resp_obj)
        else:
            return PipeResultSet(self.pipe, [])


class DmgPipeBase(PipeBase):
    """Metaclass for all pipes"""
    def __new__(cls, name, bases, attrs):
        # If this isn't a subclass of Pipe, don't do anything special.
        try:
            if not filter(lambda b: issubclass(b, DmgPipe), bases):
                return super(PipeBase, cls).__new__(cls, name, bases, attrs)
        except NameError:
            # 'Pipe' isn't defined yet, meaning we're looking at our own
            # Pipe class, defined below.
            return super(PipeBase, cls).__new__(cls, name, bases, attrs)

        # Create the class.
        new_class = type.__new__(cls, name, bases, attrs)

        mgr = DmgPipeManager()
        new_class.add_to_class('objects', mgr)
        mgr._set_pipe(new_class)

        return new_class


class DmgPipe(pipes.Pipe):
    __metaclass__ = DmgPipeBase
