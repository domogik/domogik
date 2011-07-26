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

Sms Orange Operator

Implements
==========

- SmsOrange

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

url_sms = "http://smsmms1.orange.fr/C/Sms/sms_write.php"
url_verif_auth = '^http://id.orange.fr/auth_user/bin/authNuser.cgi.*'
url_verif_sms = '^http://smsmms1.orange.fr/./Sms/sms_write.php.*'

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


    def is_on_page(self,page, page2):
        return re.search(page2, page)


    def portail_login(self,browser):
      browser.open(url_sms)
      print browser.geturl()
      if self.is_on_page(browser.geturl(),url_verif_auth):
      	post_data = {"credential" : str(self.login),
                       "pwd" : str(self.password),
                       "save_user": "false",
                       "save_pwd" : "false",
                       "save_TC"  : "true",
                       "action"   : "valider",
                       "usertype" : "",
                       "service"  : "",
                       "url"      : "http://www.orange.fr",
                       "case"     : "",
                       "origin"   : "",    }

  	post_data = urllib.urlencode(post_data)
  	browser.open(browser.geturl(), data=post_data)
  	return 1
      else:
	self.status_error = "Sms Error Login"
  	return 0

    def send_sms(self,to,body,browser):
	if self.phone_regex.match(to) is None:
		self.status_error = "Sms format to is bad"
		return 0
	if self.phone_regex.match(self.phone) is None:
		self.status_error = "Sms format phone is bad"
		return 0

  	browser.open(url_sms)
  	if self.is_on_page(browser.geturl(),url_verif_sms):
  		response = browser.response()
  		response.set_data(response.get_data().decode('utf-8', 'ignore') )
  		browser.set_response(response)
  		browser.select_form(name="formulaire")

  		listetel = ",,"+to
  		sender = self.phone

  		browser.new_control("hidden", "autorize",{'value':''})
  		browser.new_control("textarea", "msg", {'value':''})

  		browser.set_all_readonly(False)

  		browser["corpsms"] = body
  		browser["pays"] = "33"
  		browser["listetel"] = listetel
  		browser["reply"] = "2"
  		browser["typesms"] = "2"
  		browser["produit"] = "1000"
  		browser["destToKeep"] = listetel
  		browser["NUMTEL"] = sender
  		browser["autorize"] = "1"
  		browser["msg"] = body.encode('utf-8')
  		browser.submit()
		self.status_send = 1
		return 1
			
  	else:
		self.status_error = "Sms Error Compose and Send"
  		return 0



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

