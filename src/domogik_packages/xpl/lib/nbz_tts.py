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

Based on an external service provide by Wizz.cc.


@author: Kriss1
@copyright: (C) 2007-2012 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

import urllib2
import time


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

        def send_tts(self, server, serial, token, message, voice):
            """ Call NBZ HTTP API to send notification
                @param server : nabaztag server
                @param serial : nabaztag serial
                @param token : nabaztag token
                @param message : notification message
                @param voice : notification voice
            """
	    # Parameters
	    self._server = urllib2.quote(server)
            self._serial = urllib2.quote(serial)
            self._token = urllib2.quote(token)
            self._message = urllib2.quote(message)
            self._voice = urllib2.quote(voice)


            self._log.debug("NBZNotification:run")
            self._log.debug("NOTIF : server " + self._server)
            self._log.debug("NOTIF : serial " + self._serial)
            self._log.debug("NOTIF : token  " + self._token)
            self._log.debug("NOTIF : message " + self._message)
            self._log.debug("NOTIF : voice  " + self._voice)

            ttsurl="http://" + self._server + "&sn=" + self._serial + "&token=" + self._token + "&tts=" + self._message + "&" + self._voice
            staturl="http://" + self._server + "&sn=" + self._serial + "&token=" + self._token + "&action=7&silent&strip"
            wakupurl="http://" + self._server + "&sn=" + self._serial + "&token=" + self._token + "&action=13&silent&strip"
            sleepurl="http://" + self._server + "&sn=" + self._serial + "&token=" + self._token + "&action=14&silent&strip"
            chorurl="http://" + self._server + "&sn=" + self._serial + "&token=" + self._token + "&chor=10,0,motor,1,20,0,0,0,motor,0,20,0,0,1,led,0,0,238,0"

            self._log.debug("call state on nabaztag : " + staturl)
            statreq = urllib2.Request(staturl)
            try:
                stathandle = urllib2.urlopen(statreq)
            except URLError as err:
                self._log.debug("Can not connect to Wizz.cc\'s server.        \nReason : ", err.reason)
                return False
            except HTTPError as err:
                self._log.debug("Wizz.cc\'s server was unable to satify your demand.        \nError code : ",  err.code)
                return False
            else:
                statres = stathandle.read()
                self._log.debug("Wizz.cc\'s response :\n        " + statres )
                if statres == 'YES':
                    self._log.debug("call wakup on nabaztag : " + wakupurl)
                    wakupreq = urllib2.Request(wakupurl)
                    try:
                        wakuphandle = urllib2.urlopen(wakupreq)
                    except URLError as err:
                        self._log.debug("Can not connect to Wizz.cc\'s server.        \nReason : ", err.reason)
                        return False
                    except HTTPError as err:
                        self._log.debug("Wizz.cc\'s server was unable to satify your demand.        \nError code : ",  err.code)
                        return False
                    else:
                        wakupres = wakuphandle.read()
                        self._log.debug("Wizz.cc\'s response :\n        " + wakupres )
                        time.sleep(2)
                    self._log.debug("call TTS : " + ttsurl)
                    ttsreq = urllib2.Request(ttsurl)
                    try:
                        ttshandle = urllib2.urlopen(ttsreq)
                    except URLError as err:
                        self._log.debug("Can not connect to Wizz.cc\'s server.        \nReason : ", err.reason)
                        return False
                    except HTTPError as err:
                        self._log.debug("Wizz.cc\'s server was unable to satify your demand.        \nError code : ",  err.code)
                        return False
                    else:
                        ttsres = ttshandle.read() 
                        self._log.debug("Wizz.cc\'s response :\n        " + ttsres )
                    self._log.debug("call sleep on nabaztag : " + sleepurl)
                    sleepreq = urllib2.Request(sleepurl)
                    try:
                        sleephandle = urllib2.urlopen(sleepreq)
                    except URLError as err:
                        self._log.debug("Can not connect to Wizz.cc\'s server.        \nReason : ", err.reason)
                        return False
                    except HTTPError as err:
                        self._log.debug("Wizz.cc\'s server was unable to satify your demand.        \nError code : ",  err.code)
                        return False
                    else:
                        sleepres = sleephandle.read() 
                        self._log.debug("Wizz.cc\'s response :\n        " + sleepres )
                else:
                    self._log.debug("call TTS : " + ttsurl)
                    ttsreq = urllib2.Request(ttsurl)
                    try:
                        ttshandle = urllib2.urlopen(ttsreq)
                    except URLError as err:
                        self._log.debug("Can not connect to Wizz.cc\'s server.        \nReason : ", err.reason)
                        return False
                    except HTTPError as err:
                        self._log.debug("Wizz.cc\'s server was unable to satify your demand.        \nError code : ",  err.code)
                        return False
                    else:
                        ttsres = ttshandle.read() 
                        self._log.debug("Wizz.cc\'s response :\n        " + ttsres )


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
    my_nbz = NBZNotification(l)
    my_nbz.send_tts('002185ba61d4', '19644f493495351f9d427000ae070866', 'Bonjour toi', 'ws_kajedo=narbe')

 
