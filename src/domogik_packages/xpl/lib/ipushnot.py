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

Iphone Push Notification support

Based on external service provide by pushme.to


@author: Kriss1
@copyright: (C) 2007-2009 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

import urllib2


class IPushNotification:
        """ Class for sending notification to an Iphone/Ipad
        """

        def __init__(self, log):
            """
            Init object
            @param log : logger instance
            """
            self._log = log
	    self._log.info("IPushNotification:__init")

        def send_ipn(self, pushmenick, message, signature):
            """ Call PushMe.to HTTP API to send notification
                @param pushmenick : your pushme ID
                @param message : notification message
                @param signature : notification signature
            """
	    # Parameters
            self._pushmenick = urllib2.quote(pushmenick)
            self._message = urllib2.quote(message)
            self._signature = urllib2.quote(signature)


            self._log.debug("IPushNotification:run")
            self._log.debug("NOTIF : pushmenick  " + self._pushmenick)
            self._log.debug("NOTIF : message " + self._message)
            self._log.debug("NOTIF : signature  " + self._signature)

	    myurl="http://pushme.to/z/ajax/pushme/?nickname=" + self._pushmenick + "&signature=" + self._signature + "&message=" + self._message
	    self._log.debug("call : " + myurl)
	    req = urllib2.Request(myurl)
	    try:
	    	handle = urllib2.urlopen(req)
	    except URLError, err:
		self._log.debug("Can not connect to Pushme\'s server.        \nReason : ", err.reason)
		return False
	    except HTTPError, err:
		self._log.debug("Pushme\'s server was unable to satify your demand.        \nError code : ",  err.code)
		return False
	    else:
		self._log.debug("Pushme\'s response :\n        " + handle.read() )
		return True


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
    my_ipn = IPushNotification(l)
    my_ipn.send_ipn('krissdomogik', 'Alerte ! Une intrusion est detectee dans la cuisine.', 'DomogikServer')

 
