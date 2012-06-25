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
import urllib2
import time
import random
import hashlib
import base64
import re
import time
from xml.dom.minidom import parse, parseString
from threading import *

APIKEY= '98df6205-9cd3-4579-883b-51c7b6095e95'
SECRET= '8666cd42-e664-49ab-b789-7cc24c754253'
APIKAROTZ = 'http://api.karotz.com/api/karotz/'


class Karotz:
    def __init__(self,log,instid):
        self.INSTALLID=instid
        self._log = log
        self._log.debug("Karotz lib init installid: %s" % instid )
        self.interactiveId = ""
        self.stopInteractiveTimer = None

        self.keepInteractiveDelay = 10
    
    def restApiCall(self,cmd):
        url = APIKAROTZ + cmd
        
        self._log.debug(">> HTTP %s" % url)
        
        try: 
            req = urllib2.urlopen(url)
            
        except urllib2.URLError, e:
            if hasattr(e, 'reason'):
                self._log.error("Exception URLError, reason: "+  e.reason)
            elif hasattr(e, 'code'):
                self._log.error("Exception URLError, code: %d " % e.code)
            else:
                self._log.error("Exception URLError")
            return ""
        except urllib2.HTTPError, err:
            self._log.error("Http Error, errCode %d" %  err.code)
            return ""
        except:
            self._log.error("Http OtherError")
            return ""
        else:
            response = req.read()
            self._log.debug("<< HTTP %s" % response)    
            return response
    
    # sign parameters in alphabetical order
    def sign(self,parameters, signature):
        keys = parameters.keys()
        keys.sort()
        sortedParameters = [(key, parameters[key]) for key in keys]
        query = urllib.urlencode(sortedParameters)
        digest_maker = hmac.new(signature, query, hashlib.sha1)
        signValue = base64.b64encode(digest_maker.digest())
        query = query + "&signature=" + urllib.quote(signValue)
        return query

    # parse interactiveId from XmlResult
    def getInteractiveId(self,xmlString):
        try:
            doc = parseString(xmlString)
            return doc.getElementsByTagName("VoosMsg")[0].getElementsByTagName("interactiveMode")[0].getElementsByTagName("interactiveId")[0].firstChild.nodeValue
        except Exception as e:
             self._log.error("unable to parse interactiveId")
             return ""

    #parse response code: OK or KO
    def getResponseCode(self,xmlString):
        try:
            doc = parseString(xmlString)
            return doc.getElementsByTagName("VoosMsg")[0].getElementsByTagName("response")[0].getElementsByTagName("code")[0].firstChild.nodeValue
        except Exception as e:
             self._log.error("unable to parse response code")
             return ""
        
    # start interactive         
    def start(self):

        if (not self.interactiveId == ""):
            self._log.debug("start skip, already interactiveid=%s",self.interactiveId)
            return True            
        
        self.parameters = {}
        self.parameters['installid'] = self.INSTALLID
        self.parameters['apikey'] = APIKEY
        self.parameters['once'] = "%d" % random.randint(100000000, 99999999999)
        self.parameters['timestamp'] = "%d" % time.time()
        self.interactiveId = ""


        self.query = self.sign(self.parameters, SECRET)
        
        xmlResponse = self.restApiCall("start?%s" % self.query)
        
        interactiveId = self.getInteractiveId(xmlResponse)
        if interactiveId == '':
            self._log.error("start failed, unable to retrieve interactiveid")
            return False
     
        self.interactiveId=interactiveId
        self._log.debug("start succeeded, interactiveid=%s",self.interactiveId)
        return True

    def stopInteraction(self):
        xmlResponse = self.restApiCall("interactivemode?action=stop&interactiveid=%s" % self.interactiveId)
        self._log.debug("RESPONSE CODE : %s " % self.getResponseCode(xmlResponse) )
        self.interactiveId = ""
        

    # memorize end of interaction (
    def stop(self):
        
        if (self.interactiveId  == ""):
            self._log.debug("Stop interactiveMode : ignore (no interactiveId)")
            return
        
        if self.stopInteractiveTimer:
            self._log.info("Found timer, cancel...")
            self.stopInteractiveTimer.cancel()
        self._log.debug("Start timer %d sec... " % self.keepInteractiveDelay)
        self.stopInteractiveTimer = Timer(self.keepInteractiveDelay , self.stopInteraction )
        self.stopInteractiveTimer.start()
                                
    def tts(self,txt,lg):
        
        if self.start():

            params = urllib.urlencode({'action': 'speak', 'lang': lg, 'text': txt, 'interactiveid': self.interactiveId})
            xmlResponse = self.restApiCall("tts?%s" % params)
            responseCode = self.getResponseCode(xmlResponse)
            self._log.debug("RESPONSE CODE : %s " % responseCode ) 
            
            self.stop()
        
    def led(self,color,duration):
        if self.start():
            self.restApiCall("led?action=light&color=" + color + "&interactiveid=%s" % self.interactiveId)
            time.sleep(int(duration))

   
    def ears(self,right,left):
        if self.start():
           self.restApiCall("ears?left=" + left + "&right=" + right + "&reset=false&interactiveid=%s" % self.interactiveId)
            
