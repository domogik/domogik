#!/usr/bin/python
# -*- coding: latin-1 -*-

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

Karotz support. www.karotz.com

@author: Cedric BOLLINI <cb.dev@sfr.fr>
@copyright: (C) 2007-2012 Domogik project
@license: GPL(v3)

"""

import hmac
import urllib
import time
import random
import hashlib
import base64
import re
import time

APIKEY= '98df6205-9cd3-4579-883b-51c7b6095e95'
SECRET= '8666cd42-e664-49ab-b789-7cc24c754253'
#INSTALLID = 'c3c29ee3-ced6-48d3-b18b-77cc43caba72'

# sign parameters in alphabetical order
def sign(parameters, signature):
    keys = parameters.keys()
    keys.sort()
    sortedParameters = [(key, parameters[key]) for key in keys]
    query = urllib.urlencode(sortedParameters)
    digest_maker = hmac.new(signature, query, hashlib.sha1)
    signValue = base64.b64encode(digest_maker.digest())
    query = query + "&signature=" + urllib.quote(signValue)
    return query

class Karotz:
    def __init__(self,log,instid):
        self.INSTALLID=instid
        self._log = log
        
    def tts(self,txt,lg):
        #try:
        self.parameters = {}
        self.parameters['installid'] = self.INSTALLID
        self.parameters['apikey'] = APIKEY
        self.parameters['once'] = "%d" % random.randint(100000000, 99999999999)
        self.parameters['timestamp'] = "%d" % time.time()

        query = sign(self.parameters, SECRET)
        #print query

        f = urllib.urlopen("http://api.karotz.com/api/karotz/start?%s" % query)
        token = f.read() # should return an hex string if auth is ok, error 500 if not
        #print token

        data=re.findall(r'<(.*?)>(.*?)</.*?>', token)

        for elmt in data:
            if elmt[0]=='interactiveId':
	           #print elmt[1]
	           intid=elmt[1]

        f = urllib.urlopen("http://api.karotz.com/api/karotz/tts?action=speak&lang=" + lg + "&text=" + txt + "&interactiveid=%s" % intid)
        token = f.read()
        #print token

        time.sleep(2)

        f = urllib.urlopen("http://api.karotz.com/api/karotz/interactivemode?action=stop&interactiveid=%s" % intid)
        token = f.read()
        #print token