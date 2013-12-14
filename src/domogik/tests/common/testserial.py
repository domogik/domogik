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

Purpose
=======

Tools for regression tests

Usage
=====

@author: Fritz SMH <fritz.smh@gmail.com>
@copyright: (C) 2007-2012 Domogik project
@license: GPL(v3)
@organization: Domogik
"""


import time
import binascii
import json
import traceback


# for compatibility
PARITY_NONE = None
STOPBITS_ONE = None



class SerialException(Exception):
    def __init__(self, value):
        Exception.__init__(self)
        self.value = value

    def __str__(self):
        return repr(self.value)


class Serial():
    """ serial mock
    """

    def __init__(self, device, baudrate = None, parity = None, stopbits = None, timeout = None):
        """ Construtor
            @param device : the json file with the fake data
            @param baudrate : useless, just for compatibility
            @param parity : useless, just for compatibility
            @param stopbits : useless, just for compatibility
            @param timeout : useless, just for compatibility
        """
        # there is nothing to do, excepting logging!
        print(u"Fake serial device created. The fake data in the file '{0}' will be used".format(device))

        # load the json file
        try:
            json_fp = open(device)
            self.data = json.load(json_fp)
            json_fp.close()
        except:
            raise SerialException(u"Error while opening fake serial device from file {0} : {1}".format(device, traceback.format_exc()))
        
        # read index
        self.history_idx = 0
        # loop index
        self.loop_idx = 0

    def flush(self):
        pass

    def close(self):
        pass

    def write(self, data):
        """ Mock for input data on the serial device
        """
 
        # TODO : respond with the appropriate answers depending on what has been write to the fake serial device
        pass

    def read(self, length = 1):
        """ Mock the read feature
            @param length : length of the data to read. For compatibility only
        """        
        while True:
            # check if we are waiting for some response 
            #TODO

            # handle the history part
            if self.history_idx < len(self.data['history']):
                action = self.data['history'][self.history_idx]['action']
                description = self.data['history'][self.history_idx]['description']
                print(u"Action = {0} / Description = {1}".format(action, description))
                if action == 'data':
                    value = binascii.unhexlify(self.data['history'][self.history_idx]['data'])
                    self.history_idx += 1
                    return value
                if action == 'wait':
                    delay = self.data['history'][self.history_idx]['delay']
                    print(u" => wait for {0}s".format(delay))
                    self.history_idx += 1
                    time.sleep(delay)
            # and if the history is finished, handle the loop
            else:
                if self.data['loop'] == []:
                    raise SerialException(u"There is nothing else to read in the fake serial device")
                else:
                    print("The history has ended...we are in the loop")
                    if self.loop_idx == len(self.data['loop']):
                        self.loop_idx = 0
                    action = self.data['loop'][self.loop_idx]['action']
                    description = self.data['loop'][self.loop_idx]['description']
                    print(u"Action = {0} / Description = {1}".format(action, description))
                    if action == 'data':
                        value = binascii.unhexlify(self.data['loop'][self.loop_idx]['data'])
                        self.loop_idx += 1
                        return value
                    if action == 'wait':
                        delay = self.data['loop'][self.loop_idx]['delay']
                        print(u" => wait for {0}s".format(delay))
                        self.loop_idx += 1
                        time.sleep(delay)
               


if __name__ == "__main__":

    my_mock = Serial("/media/stock/domotique/git/domogik-plugin-rfxcom/tests/352_data.json")
    while True:
        my_mock.read()


# TODO :
# add a dictionnary to respond
