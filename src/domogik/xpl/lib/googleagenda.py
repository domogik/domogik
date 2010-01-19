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

Module purpose
==============

Google Agenda : get today's events

Implements
==========

- GAgenda.__init__
- GAgenda._connect
- GAgenda._get_today_events
- GAgenda._get_tomorrow_events
- GAgenda.__get_events

@author: Fritz <fritz.smh@gmail.com>
@copyright: (C) 2007-2009 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

from domogik.common import logger
from domogik.common.ordereddict import OrderedDict

import datetime
import gdata.calendar.service


class GAgenda:
    """ 
    This class allow to get events from Google Agenda
    """

    def __init__(self, email, password, calendar_name, callback):
        """ @param email : email of gmail account
        @param password : password for account
        @param calendar_name : name of calendar to check (by default, it has email value)
        @param callback : callback for sending events found
        """

        # Init logger
        l = logger.Logger('GAGENDA')
        self._log = l.get_logger()
        self._log.info("GAgenda:__init__")
        self._log.info("Email : " + email)
        self._log.info("Pass : " + password)

        # Parameters
        self._email = email
        self._password = password
        self._cb = callback



    def _connect(self):
        """
        Connect to google web services
        """
        self._log.info("GAgenda:_connect")

        self._calendar = gdata.calendar.service.CalendarService()
        self._calendar.email = self._email
        self._calendar.password = self._password
        self._calendar.source = 'Domogik'
        self._calendar.ProgrammaticLogin()


    def get_today_events(self):
        """
        Get today's events
        """
        self._log.info("GAgenda:_get_today_events")
        start_date = datetime.date.today()
        end_date = datetime.date.today() + datetime.timedelta(days=1)
        self._get_events(start_date, end_date)


    def get_tomorrow_events(self):
        """
        Get tomorrow's events
        """
        self._log.info("GAgenda:_get_tomorrow_events")
        start_date = datetime.date.today() + datetime.timedelta(days=1)
        end_date = datetime.date.today() + datetime.timedelta(days=2)
        self._get_events(start_date, end_date)


    def get_events_at_date(self, date):
        """
        Get events of a specified date
        """
        self._log.info("GAgenda:_get_events_at_date")

        # treat requested date to make a date
        req_year = int(date[0:4])
        req_month = int(date[5:7])
        req_day = int(date[8:10])
        start_date = datetime.date(req_year, req_month, req_day)
        end_date = start_date + datetime.timedelta(days=1)

        self._get_events(start_date, end_date)



    def _get_events(self, date_min, date_max):
        """
        Get events
        """
        self._log.info("GAgenda:__get_events")
        self._log.info("date_min : " + str(date_min))
        self._log.info("date_max : " + str(date_max))

        events = []

        # Connect to google agenda
        self._connect()

        # Get todays's events
        query = gdata.calendar.service.CalendarEventQuery('default', 'private', 'full')
        query.start_min = str(date_min)
        query.start_max = str(date_max)
        feed = self._calendar.CalendarQuery(query)

        # Sort events by date/time
        event_list = sorted(feed.entry, self._sort_event) 

        # Display events
        for i, an_event in enumerate(event_list):
            futurEvent = False
            # get event data
            event_title = an_event.title.text
            event_year = int(an_event.when[0].start_time[0:4])
            event_month = int(an_event.when[0].start_time[5:7])
            event_day = int(an_event.when[0].start_time[8:10])
            event_hour = int(an_event.when[0].start_time[11:13])
            event_minute = int(an_event.when[0].start_time[14:16])
            event_datetime = datetime.datetime(event_year, event_month, event_day, event_hour, event_minute)
            # we only take futur events
            if event_datetime > datetime.datetime.now():
                futurEvent = True
                self._log.info("Event : " + event_title + " at " + str(event_datetime))
                events.append({"object" : event_title, "startdate" : event_datetime})

        # send events to callback
        if events:
            self._cb(events)
        else:
            self._log.info("No events to send")


    def _sort_event(self, x, y):
        """
        Sort events by date
        """
        xtitle = x.title.text
        ytitle = y.title.text
        x_when =  x.when[0]
        y_when =  y.when[0]
        x_start = x_when.start_time
        y_start = y_when.start_time
        if (x_start > y_start):
            return 1
        elif (x_start < y_start):
            return -1
        else:
            return 0 




def cb(data):
    print "DATA : " 
    print data


if __name__ == "__main__":
    g = GAgenda("fritz.smh@gmail.com", "XXXXXXXX", "fritz.smh@gmail.com", cb)
    print "Today :"
    g.get_today_events()
    print "Tomorrow :"
    g.get_tomorrow_events()
