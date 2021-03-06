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

@author: Fritz SMH <fritz.smh@gmail.com>
@copyright: (C) 2007-2015 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

from domogik.scenario.actions.abstract import AbstractAction
import time
import threading
import traceback


class PauseAction(AbstractAction):
    """ Do a pause between 2 actions
    """

    def __init__(self, log=None, params=None):
        AbstractAction.__init__(self, log)
        self.set_description(u"Do a pause (>=1s).")
        self.the_end = None
        self._timer = None

    def do_action(self):
        try:
            delay = float(self._params['delay'])
            self._log.info(u"Do a pause of {0} seconds".format(delay))
            self.the_end = threading.Event()
            self._timer = threading.Timer(int(delay), self.end_waiting, [])
            self._timer.start()
            started = time.time()
            __delay = 0.01
            __subdelay = (delay / 10)
            if __subdelay < 1 : __subdelay = 1
            __factdelay = __subdelay/ __delay
            __cpt = 0
            while (self._timer is not None and self.the_end is not None) and not self.the_end.is_set() :
                if __cpt % (__factdelay) == 0.0 : # Display only seconds
                    self._log.debug(u"Paused since {0} s / {1} s ...".format(int(time.time() - started), delay))
                self.the_end.wait(__delay)
                __cpt += 1;
        except:
            self._log.error(u"Error while casting delay '{0}' to int value. Full error is : {1}".format(delay, traceback.format_exc()))
        self._log.info(u"Pause of {0} seconds finished".format(delay))
        self.the_end = None

    def end_waiting(self):
        if self._timer is not None :
            self._log.debug(u"Cancel timer.")
            self._timer.cancel()
        if self.the_end is not None:
            self._log.debug(u"End waiting...")
            self.the_end.set()
        self._timer = None

    def destroy(self):
        AbstractAction.destroy(self)
        self.end_waiting()

    def get_expected_entries(self):
        return {'delay': {'type': 'integer',
                            'description': 'Delay in seconds',
                            'default': '5'}
               }


if __name__ == "__main__":
    P = PauseAction()
    P.do_action()
