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

- Events management

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



class DmgEvents():
    """
    Object where all events queues and ticket id will be stored
    """
    def __init__(self, get_stop, log, event_timeout, queue_size, queue_timeout, queue_life_expectancy):
        """ Init Event Requests
            @param queue_size : size of queues for events
        """
        self.requests = {}
        self.get_stop = get_stop
        self._log = log
        self.event_timeout = event_timeout
        self.queue_size = queue_size
        if queue_timeout == 0:
            self.queue_timeout = None
        else:
            self.queue_timeout = queue_timeout
        self.queue_life_expectancy = queue_life_expectancy
        self.ticket = 0
        self.count_request = 0

        # Launch background cleaning function
        self._stop_clean = Event()
        bg_clean = Thread(None, self.bg_clean_event_requests, 'rest_clean_event', (), {})
        bg_clean.start()

    def bg_clean_event_requests(self):
        """ Function to use in background. It will check for each request to see
            if it has not be forgoten to clean
        """
        while not self._stop_clean.isSet():
            clean_list = []
            for req in self.requests:
                if time.time() - self.requests[req]["last_access_date"] > self.event_timeout:
                    print("Ticket number '%s' expires : it will be deleted" % req)
                    clean_list.append(req)
            for req in clean_list:
                del self.requests[req]
                self.count_request -= 1
            self._stop_clean.wait(30)

    def set_stop_clean(self):
        """ Set the event use by bg_clean_event_requests to stop it 
        """
        self._stop_clean.set()

    def new(self):
        """ Add a new queue and ticket id for a new event
            @return ticket_id : ticket id
        """
        print("---- NEW ----")
        new_queue = Queue(self.queue_size)
        ticket_id = self.generate_ticket()
        cur_date = time.time()
        new_data = {"creation_date" :  cur_date,
                    "last_access_date" : cur_date,
                    "queue" : new_queue,
                    "queue_size" : 0}
        self.requests[ticket_id] = new_data
        self.count_request += 1
        self._log.debug("New event created (ticket_id=%s)" % ticket_id)
        return ticket_id

    def free(self, ticket_id):
        """ End request for a ticket id : remove queue
            @param ticket_id : ticket id of queue to remove
            @return True if succcess, False if ticket doesn't exists
        """
        try:
            del self.requests[ticket_id]
        # ticket doesn't exists
        except KeyError:
            self._log.warning("Trying to free an unknown event request (ticket_id=%s)" % ticket_id)
            return False
        self.count_request -= 1
        return True

    def generate_ticket(self):
        """ Generate a ticket id for an event request
        """
        # TODO : make something random for ticket generation after 0.1.0
        self.ticket += 1
        return str(self.ticket)
 
    def count(self):
        """ Return number of event requests
        """
        return self.count_request

    def add_in_queues(self, data):
        """ Add data in each queue linked to device id
            @param data : data to put in queues
        """
        print("---- ADD ----")
        for req in self.requests:
            ### clean queue
            idx = 0
            queue_size = self.requests[req]["queue"].qsize()
            actual_time = time.time()
            while idx < queue_size:
                if self.requests[req]["queue"].empty() == False:
                    (elt_time, elt_data) = self.requests[req]["queue"].get_nowait()
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


    def get(self, ticket_id):
        """ Get data from queue linked to ticket id. 
            If no data, wait until queue timeout
            @param ticket_id : id of ticket
            @return data in queue or False if ticket doesn't exists
        """
        print("---- GET ----")
        x = 0
        empty = True
        while not self.get_stop().isSet() and x < (self.queue_timeout) and empty == True:
            x = x + 0.1
            try:
                (elt_time, elt_data) = self.requests[ticket_id]["queue"].get_nowait()
                empty = False

            # No data
            except Empty:
                empty = True
                self.get_stop().wait(0.1)

            # Ticket doesn't exists
            except KeyError:
                self._log.warning("Trying to get an unknown event request (ticket_id=%s). Maybe your ticket expires ?" % ticket_id)
                return False


        if empty == True:
            # Add ticket id to answer
            elt_data = {}
            elt_data["ticket_id"] = str(ticket_id)

            # Update access date
            self.requests[ticket_id]["last_access_date"] = time.time()

            return elt_data

        else:
            self.requests[ticket_id]["queue_size"] -= 1
            # TODO : use queue_life_expectancy in order not to get old data

            # Add ticket id to answer
            #elt_data = {}
            elt_data["ticket_id"] = str(ticket_id)

            # Update access date
            self.requests[ticket_id]["last_access_date"] = time.time()

            print(elt_data)
            return elt_data

    def stop_get(self):
        """ Set the flag for while get_nowait to False
        """
        self.listen_queue = False

    def list(self):
        """ List queues (used by rest status)
        """
        return self.requests

