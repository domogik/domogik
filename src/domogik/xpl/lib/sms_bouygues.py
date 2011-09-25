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

Sms Bouygues Operator

Implements
==========

- Sms

@author: Gizmo  - Guillaume MORLET <contact@gizmo-network.fr>
@copyright: (C) 2007-2011 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

import sys
import mechanize
import cookielib
import urllib
import re

url_sms = "http://www.espaceclient.bouyguestelecom.fr/ECF/jsf/client/envoiSMS/viewEnvoiSMS.jsf"
url_sms2 = 'http://www.mobile.service.bbox.bouyguestelecom.fr/services/SMSIHD/sendSMS.phtml'
url_confirm = 'http://www.sfr.fr/xmscomposer/mc/envoyer-texto-mms/confirm.html'
service_url = 'http://www.sfr.fr/xmscomposer/j_spring_cas_security_check'
url_verif_auth = 'https://www.sfr.fr/cas/login?service=http%3A%2F%2Fwww.sfr.fr%2Fxmscomposer%2Fj_spring_cas_security_check'

class Sms:
    """ Sms Control
    """
    phone_regex = re.compile('^(\+33|0033|0)(6|7)(\d{8})$')

    def __init__(self, log = None,login = None,password = None,phone = None):
        """ Init SMS Operator
        """
        self._log = log
       	self.login = login
       	self.password =password
	self.phone = phone
	self.status_send = 0
	self.status_error = ""


    def portail_login(self,browser):
      	browser.open(url_sms)
      	print browser.geturl()
	for x in browser.forms():
        	print x	
        browser.select_form(name='code')
        browser['j_username'] = login
        browser['j_password'] = password
        browser.submit()

        return 1
	

    def send_sms(self,to,body,browser):
	print "sms_send : entrée"
	if self.phone_regex.match(to) is None:
		self.status_error = "Sms format to is bad"
		return 0
	if self.phone_regex.match(self.phone) is None:
		self.status_error = "Sms format phone is bad"
		return 0

  	browser.open(url_sms2)
	print "sms_send : formulaire sms"
	for x in browser.forms():
        	print x	
	browser.select_form(nr=0)
        browser['fieldMsisdn'] = to
        browser['fieldMessage'] = body.encode('utf-8')
        browser.submit()
	print "sms_send : confirmation sms"


	self.status_send = 1
	return 1


    def send(self, to, body):
        """ Send Sms
            @param to : receiver
            @param body : message
        """
        br = mechanize.Browser()

	br.set_handle_equiv(True)
	br.set_handle_robots(False)
	br.set_handle_referer(True)
	br.set_handle_refresh(True)
	br.set_handle_redirect(True)
	
        cj = cookielib.LWPCookieJar()
	br.set_cookiejar(cj)
        #self.log.debug("call back5")
        print "function Sms Send : before portail_login"
    	if self.portail_login(br):
           print "function Sms Send : between portail_login and send_sms"
	   self.send_sms(to,body,br)
	   print "function Sms Send : after send_sms"
	
	else:
	   print "function portail_login : error"



if __name__ == "__main__":
    my_sms = Sms(None)

