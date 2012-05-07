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

Android Push Notification support

Based on external service provide by pushme.to


@author: Kriss1
@copyright: (C) 2007-2012 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

import urllib
import urllib2
import json

# Configuration.
BACKEND = 'https://notifrier.appspot.com/notifry';


class APushNotification:
        """ Class for sending notification to an Android device
        """

        def __init__(self, log):
            """
            Init object
            @param log : logger instance
            """
            self._log = log
	    self._log.info("APushNotification:__init")

        def send_apn(self, source, title, message):
            """ Call Notifry HTTP API to send notification
                @param source : your Notifry ID
		@param title : notification title
                @param message : notification message
            """
	    # Parameters
            params = {}
            params['format'] = 'json' # only json is supported for the moment
	    params['source'] = source
	    params['title'] = title
	    params['message'] = message

            self._log.debug("APushNotification:run")
            self._log.debug("NOTIF : params : " + str(params))
	    req = urllib2.Request(BACKEND, urllib.urlencode(params))
	    self._log.debug("call : " + BACKEND + " with " + str(params) + " parameters.")

	    # Prepare our request.
	    try:
		response = urllib2.urlopen(req)

		# Read the body.
		body = response.read()
		# It's JSON - parse it.
		contents = json.loads(body)

		if contents.has_key('error'):
			self._log.debug("Notifry\'s Server did not accept our message: %s" % contents['error'])
			#return False
		else:
			self._log.debug("Notifry\'s response :\n Message sent OK. Size: %d." % contents['size'])
			#return True

	    except urllib2.URLError, ex:
		self._log.debug("Failed to make request to the Notifry\'s server: " + str(ex))
		#return False


class Log:
    def __init__(self):
        pass

    def debug(self, msg):
        print("DEBUG : %s" % msg)

    def error(self, msg):
        print("ERROR : %s" % msg)

    def warning(self, msg):
        print("WARN : %s" % msg)

    def info(self, msg):
        print("INFO : %s" % msg)


if __name__ == "__main__":
    l = Log()
    my_apn = APushNotification(l)
    my_apn.send_apn('2c749dc46381dbc3646ee87ce77184f4', 'Alerte !', 'Une intrusion est detectee dans la cuisine.')


