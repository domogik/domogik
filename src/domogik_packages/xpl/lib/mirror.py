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

Mir:ror (Violet) support

Implements
==========

- Mirror

@author: Fritz <fritz.smh@gmail.com>
@copyright: (C) 2007-2012 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

import binascii


class MirrorException(Exception):
    """
    Mirror exception
    """

    def __init__(self, value):
        Exception.__init__(self)
        self.value = value

    def __str__(self):
        return repr(self.value)


class Mirror:
    """ Helpers for Mir:ror
    """

    def __init__(self, log, callback):
        """ Init Mirror object
            @param log : log instance
            @param callback : callback
        """
        self._log = log
        self._callback = callback
        self._mirror = None

    def open(self, device):
        """ Open Mir:ror device
            @param device : mir:ror device (/dev/hidrawX)
        """
        try:
            self._log.info("Try to open Mir:ror device : %s" % device)
            self._mirror = open(device, "rb")
            self._log.info("Mir:ror device opened")
        except:
            error = "Error while opening Mir:ror device : %s. Check if it is the good device or if you have the good permissions on it." % device
            raise MirrorException(error)

    def close(self):
        """ close Mir:ror device
        """
        self._log.info("Close Mir:ror device")
        try:
            self._mirror.close()
        except:
            error = "Error while closing Mir:ror device"
            raise MirrorException(error)

    def listen(self, stop):
        """ Start listening to Mir:ror
        @param stop : an Event to wait for stop request
        """
        # listen to mir:ror
        self._log.info("Start listening Mir:ror")
        # infinite
        while not stop.isSet():
            device, my_type, current = self.read()
            if device != None:
                self._callback(device, my_type, current)

    def read(self):
        """ Read Mir:ror device once
        """
        # We read 16 byte
        data = self._mirror.read(16)
        # if the first byte is not null, this is a message
        if data[0] != '\x00':
            # first byte : action type : ztamp or action on mir:ror
            if data[0] == '\x02':
                ### action on ztamp
                # data[0] and data[1] : action type
                # data[2...15] : ztamp identifier
                #        (it seems that 2,3, 14,15 are always nulls)
                self._log.debug("Action on : ztamp")
                ztamp_id = binascii.hexlify(data[2]+data[3]+ \
                                 data[4]+data[5]+data[6]+ \
                                 data[7]+data[8]+data[9]+ \
                                 data[10]+data[11]+data[12]+ \
                                 data[13]+data[14]+data[15])
                if data[1] == '\x01':
                    self._log.debug("ztamp near from mir:ror : "+ ztamp_id)
                    return ztamp_id, "present", "high"
                if data[1] == '\x02':
                    self._log.debug("ztamp far from mir:ror : "+ ztamp_id)
                    return ztamp_id, "present", "low"

            if data[0] == '\x01':
                ### action on mir:ror
                # Only the data[0] and data[1] are used in this case
                # The others are nulls
                if data[1] == '\x04':
                    self._log.debug("Action on : mir:ror")
                    self._log.debug("mir:ror faced up")
                    return "mirror", "activated", "high"
                if data[1] == '\x05':
                    self._log.debug("Action on : mir:ror")
                    self._log.debug("mir:ror faced down")
                    return "mirror", "activated", "low"
        return None, None, None


