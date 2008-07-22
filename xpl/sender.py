#! /usr/bin/python
# -*- encoding:utf-8 -*-

# Author : Maxence Dunnewind <maxence@dunnewind.net>
# $LastChangedBy: mschneider $
# $LastChangedDate: 2008-07-22 09:33:08 +0200 (mar. 22 juil. 2008) $
# $LastChangedRevision: 98 $

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
        #Create our xPL link
        #This may raise some exception in case of network problem
        self.__xpl = Manager(ip = xplhost, port = xplport, source = xplsource)

        #The list to get messages
        self.__list = list

    def run(self):
        """
        Run the main sender stuff
