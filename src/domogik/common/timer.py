# -*- coding: utf-8 -*-

""" This file is part of B{Domogik} project (U{http://www.domogik.org}).

License
=======

B{Domogik} is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
A
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

A generic Timer class

Implements
==========

- Timer.__init__(self, time, cb, stop)
- Timer.start(self)
- Timer.getTimer(self)
- Timer.stop(self)

@author: Maikel Punie <maikel.punie@gmail.com>
@copyright: (C) 2007-2016 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

from tornado.ioloop import PeriodicCallback

class Timer(object):
    """
    Timer will call a callback function each n seconds
    """
#    _time = 0
#    _callback = None
#    _timer = None

    def __init__(self, time, callback, manager):
        """
        Constructor : create the internal timer
        @param time : time of loop in second
        @param callback : callback function which will be call eact 'time' seconds
	@param log : an logger instance
        """
        self._timer = PeriodicCallback(callback, (time*1000))
        self.log = manager.p.log
        manager.p.register_timer(self)
        self.log.debug(u"New timer created : %s " % self)

    def start(self):
        """
        Start the timer
        """
        self._timer.start()

    def get_timer(self):
        """
        Waits for the internal thread to finish
        """
        return self._timer

    def __del__(self):
        self.log.debug(u"__del__ Manager")
        self.stop()

    def stop(self):
        """
        Stop the timer
        """
        self._timer.stop()
        self.log.debug(u"Timer : stop, unregister it")
