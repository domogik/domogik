#!/usr/bin/python
# -*- encoding:utf-8 -*-

# Copyright 2008 Domogik project

# This file is part of Domogik.
# Domogik is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# Domogik is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with Domogik.  If not, see <http://www.gnu.org/licenses/>.

# Author: Maxence Dunnewind <maxence@dunnewind.net>

# $LastChangedBy: maxence $
# $LastChangedDate: 2009-01-31 13:42:51 +0100 (sam. 31 janv. 2009) $
# $LastChangedRevision: 296 $

# This is for sending xPL messages on an xPL network
# The messages are serialized (put in some list) and
# sent on the xPL network
# The UI should use this facilities to send messages
# to avoid error coming from network timeout, etc...

#Threading
import time
import threading

#xPL support
from xPLAPI import *

class Sender(threading.Thread):
    """
    This class will pick up messages from a list and send them to the network
    """

    def __init__(self, xplport, xplhost, xplsource = "domogik-ui.sender", list, lock, die):
        """
        Constructor
        @param xplport : Port of the xPL Bus
        @param xplhost : Host of the xPL Bus
        @param xplsource : Source to send message from, default 'domogik-ui.sender'
        @param list : list to take message from
        @param lock : 
		"""
        #Create our xPL link
        #This may raise some exception in case of network problem
        self.__xpl = Manager(ip = xplhost, port = xplport, source = xplsource)

        #The list to get messages
        self.__list = list

    def run(self):
        """
        Run the main sender stuff
