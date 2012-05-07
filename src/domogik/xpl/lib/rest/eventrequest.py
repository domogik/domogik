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
=============

- Events requests management

Implements
==========

EventRequests object



@author: Friz <fritz.smh@gmail.com>
@copyright: (C) 2007-2012 Domogik project
@license: GPL(v3)
@organization: Domogik
"""
import time
from Queue import Queue, Empty, Full
from threading import Thread, Event
from domogik.xpl.common.xplconnector import XplTimer
from domogik.xpl.lib.rest.event import DmgEvents


class RequestEvents(DmgEvents):
    """
    Object where all events queues and ticket id will be stored
    """

    def new(self, device_id_list):
        """ Add a new queue and ticket id for a new event
            @param device_id : id of device to get events from
            @return ticket_id : ticket id
        """
        print("---- NEW ----")
        new_queue = Queue(self.queue_size)
        ticket_id = self.generate_ticket()
        cur_date = time.time()
        new_data = {"creation_date" :  cur_date,
                    "last_access_date" : cur_date,
                    "device_id_list" : device_id_list,
                    "queue" : new_queue,
                    "queue_size" : 0}
        self.requests[ticket_id] = new_data
        self.count_request += 1
        self._log.debug("New event request created (ticket_id=%s) for device(s) : %s" % (ticket_id, str(device_id_list)))
        return ticket_id

    def add_in_queues(self, device_id, data):
        """ Add data in each queue linked to device id
            @param data : data to put in queues
        """
        print("---- ADD ----")
        for req in self.requests:
            if device_id in self.requests[req]["device_id_list"]:
                ### clean queue
                idx = 0
                queue_size = self.requests[req]["queue"].qsize()
                actual_time = time.time()
                while idx < queue_size:
                    if self.requests[req]["queue"].empty() == False:
                        (elt_time, elt_data) = self.requests[req]["queue"].get_nowait()
                        # if there is already data about device_id, we clean it (we don't put it back in queue)
                        # or if data is too old
                        # Note : if we get new stats only each 2 minutes, 
                        #     cleaning about life expectancy will only happen 
                        #     every 2 minutes instead of every 'life_expectancy'
                        #     seconds. I supposed that when you got several 
                        #     technologies, you pass throug this code several 
                        #     times in a minute. More over,  events are
                        #     actually (0.1) used only by UI and when you use
                        #     UI, events are read immediatly. So, I think
                        #     that cleaning queues here instead of creating
                        #     a dedicated process which will run in background
                        #     is a good thing for the moment
                        if elt_data["device_id"] != device_id and \
                           actual_time - elt_time < self.queue_life_expectancy:

                            self.requests[req]["queue"].put((elt_time, elt_data),
                                                            True, self.queue_timeout) 
                        else:
                            # one data suppressed from queue
                            self.requests[req]["queue_size"] -= 1
                        
                    idx += 1

                ### put data in queue
                try:
                    self.requests[req]["queue"].put((time.time(), data), 
                                                    True, self.queue_timeout) 
                    self.requests[req]["queue_size"] += 1
                except Full:
                    self._log.error("Queue for ticket_id '%s' is full. Feel free to adjust Event queues size" % req)


