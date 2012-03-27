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

Google Agenda

Implements
==========

- GAgendaListener

@author: Fritz <fritz.smh@gmail.com>
@copyright: (C) 2007-2012 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

from domogik.xpl.lib.gagenda import GAgenda
from domogik.xpl.common.xplconnector import Listener
from domogik.xpl.common.xplmessage import XplMessage
from domogik.xpl.common.plugin import XplPlugin
from domogik.xpl.common.queryconfig import Query



class GAgendaListener(XplPlugin):
    """ Listen for xPL messages to get infos from agenda
    """

    def __init__(self):
        """ Create lister for google agenda requets
        """
        XplPlugin.__init__(self, name = 'gagenda')

        # Create logger
        self.log.debug("Listener for Google agenda created")

        # Get config
        self._config = Query(self.myxpl, self.log)
        self._email = self._config.query('gagenda', 'email')
        self._password = self._config.query('gagenda', 'password')
        self._calendar_name = self._config.query('gagenda', 'calendarname')

        # Create object
        self._gagenda_manager = GAgenda(self.log, \
                                       self._email, \
                                       self._password, \
                                       self._calendar_name, \
                                       self._broadcast_events)

        # Create listener for today
        Listener(self.gagenda_cb, self.myxpl, {'schema': 'calendar.request',
                'xpltype': 'xpl-cmnd', 'command': 'REQUEST'})
        self.enable_hbeat()

    def gagenda_cb(self, message):
        """ Call google agenda lib
            @param message : xlp message received
        """
        self.log.debug("Call gagenda_cb")
        if 'command' in message.data:
            command = message.data['command']
        if 'date' in message.data:
            date = message.data['date']

        # if it is a request command
        if command == "REQUEST":
            self.log.debug("Google agende request command received for " + \
                            str(date))
            if date == "TODAY":
                self._gagenda_manager.get_today_events()
            elif date == "TOMORROW":
                self._gagenda_manager.get_tomorrow_events()
            else:
                self._gagenda_manager.get_events_at_date(date)


    def _broadcast_events(self, events):
        """ Send xPL message on network
            @param events : list of events
        """
        for entry in events:
            my_temp_message = XplMessage()
            my_temp_message.set_type("xpl-trig")
            my_temp_message.set_schema("calendar.basic")
            print("entry = ")
            print(entry)
            my_temp_message.add_data({"object" : entry["object"]})
            my_temp_message.add_data({"startdate" : entry["startdate"]})
            self.myxpl.send(my_temp_message)


if __name__ == "__main__":
    GAL = GAgendaListener()

