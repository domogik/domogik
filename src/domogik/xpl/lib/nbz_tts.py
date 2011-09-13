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

Nabaztag TTS support

Based on an external service provide by Mindscape.


@author: Kriss1
@copyright: (C) 2007-2009 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

import urllib2


class NBZNotification:
        """ Class for sending message to a Nabaztag
        """

        def __init__(self, log):
            """
            Init object
            @param log : logger instance
            """
            self._log = log
	    self._log.info("NBZNotification:__init")

        def send_tts(self, serial, token, message, voice):
            """ Call NBZ HTTP API to send notification
                @param serial : nabaztag serial
                @param token : nabaztag token
                @param message : notification message
                @param voice : notification voice
            """
	    # Parameters
            self._serial = urllib2.quote(serial)
            self._token = urllib2.quote(token)
            self._message = urllib2.quote(message)
            self._voice = urllib2.quote(voice)


            self._log.debug("NBZNotification:run")
            self._log.debug("NOTIF : serial " + self._serial)
            self._log.debug("NOTIF : token  " + self._token)
            self._log.debug("NOTIF : message " + self._message)
            self._log.debug("NOTIF : voice  " + self._voice)

	    myurl="http://api.wizz.cc/?sn=" + self._serial + "&token=" + self._token + "&tts=" + self._message + "&" + self._voice
	    self._log.debug("call : " + myurl)
	    req = urllib2.Request(myurl)
	    try:
	    	handle = urllib2.urlopen(req)
	    except URLError, err:
		self._log.debug("Can not connect to Mindscape\'s server.        \nReason : ", err.reason)
		return False
	    except HTTPError, err:
		self._log.debug("Mindscape\'s server was unable to satify your demand.        \nError code : ",  err.code)
		return False
	    else:
		self._log.debug("Mindscape\'s response :\n        " + handle.read() )
		return True


class Log:
    def __init__(self):
        pass

    def debug(self, msg):
        print "DEBUG : %s" % msg

    def error(self, msg):
        print "ERROR : %s" % msg

    def warning(self, msg):
        print "WARN : %s" % msg

    def info(self, msg):
        print "INFO : %s" % msg


if __name__ == "__main__":
    l = Log()
    my_nbz = NBZNotification(l)
    my_nbz.send_tts('002185ba61d4', '19644f493495351f9d427000ae070866', 'Bonjour mon coeur', 'ws_kajedo=narbe')

 
