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


### for compatibility
# taken from /usr/lib/python2.7/dist-packages/serial/serialutil.py

def to_bytes(seq):
    """convert a sequence to a bytes type"""
    b = bytearray()
    for item in seq:
        b.append(item)  # this one handles int and str
    return bytes(b)

# create control bytes
XON  = to_bytes([17])
XOFF = to_bytes([19])

CR = to_bytes([13])
LF = to_bytes([10])

PARITY_NONE, PARITY_EVEN, PARITY_ODD, PARITY_MARK, PARITY_SPACE = 'N', 'E', 'O', 'M', 'S'
STOPBITS_ONE, STOPBITS_ONE_POINT_FIVE, STOPBITS_TWO = (1, 1.5, 2)
FIVEBITS, SIXBITS, SEVENBITS, EIGHTBITS = (5, 6, 7, 8)

### end compatibility



class SerialException(Exception):
    def __init__(self, value):
        Exception.__init__(self)
        self.value = value

    def __str__(self):
        return repr(self.value)


class Serial():
    """ serial mock
    """

    def __init__(self, port, baudrate = None, bytesize = None, parity = None, stopbits = None, timeout = None, xonxoff = None, rtscts = None, writeTimeout = None, dsrdtr = None, interCharTimeout = None):
        """ Construtor
            @param port : the json file with the fake data
            @param baudrate : useless, just for compatibility
            @param bytesize : useless, just for compatibility
            @param parity : useless, just for compatibility
            @param stopbits : useless, just for compatibility
            @param timeout : useless, just for compatibility
            @param ... : useless, just for compatibility
        """
        # there is nothing to do, excepting logging!
        print(u"Fake serial device created. The fake data in the file '{0}' will be used".format(port))

        # load the json file
        try:
            json_fp = open(port)
            self.data = json.load(json_fp)
            json_fp.close()
        except:
            raise SerialException(u"Error while opening fake serial device from file {0} : {1}".format(port, traceback.format_exc()))
        
        # read index
        self.history_idx = 0
        # loop index
        self.loop_idx = 0

        # set a flag for the first read 
        self.first_read = True

        # set the next_response (used by write function) to None
        self.next_responses = None

    def flush(self):
        pass

    def close(self):
        pass

    def write(self, data):
        """ Mock for input data on the serial device
            respond with the appropriate answers depending on what has been write to the fake serial device
        """
 
        found = False
        for mock in self.data['responses']:
            if mock['type'] == "data":
                if data == mock['when']:
                    found = True
                    responses = mock['do']
                    data_for_log = data
            elif mock['type'] == "data-hex":
                if binascii.hexlify(data).lower() == mock['when'].lower():
                    found = True
                    responses = mock['do']
                    data_for_log = binascii.hexlify(data)
        if found:
            print(u"Found mock responses for data written : {0}. Response is {1}".format(data_for_log, responses))
            self.next_responses = responses

    def readline(self, length = 1):
        return self.read(length)

    def read(self, length = 1):
        """ Mock the read feature
            @param length : length of the data to read. For compatibility only
        """        
        if self.first_read:
            # first, wait for 30 seconds
            # this allows to be sure that the plugin is fully ready before using the fake serial device
            print("Before the first read, we wait for 30 seconds...")
            time.sleep(30)
            self.first_read = False

        while True:

            # handle a response to a write action
            if self.next_responses != None:
                response = self.next_responses[0]
                if response['type'] == "data-hex":
                    print(u"Action = reply to a write action / Delay = {0} / Data = {1}".format(response['delay'], response['data']))
                    data = binascii.unhexlify(response['data'])
                elif response['type'] == "data":
                    print(u"Action = reply to a write action / Delay = {0} / Data = {1}".format(response['delay'], binascii.hexlify(response['data'])))
                    data = response['data']

                time.sleep(int(response['delay']))
                # remove first item from the responses list
                self.next_responses.pop(0)
                if self.next_responses == []:
                    self.next_responses = None
                return data

            # handle the history part
            elif self.history_idx < len(self.data['history']):
                action = self.data['history'][self.history_idx]['action']
                description = self.data['history'][self.history_idx]['description']
                print(u"Action = {0} / Description = {1}".format(action, description))
                if action == 'data':
                    value = self.data['history'][self.history_idx]['data']
                    print(value)
                    self.history_idx += 1
                    return value
                elif action == 'data-hex':
                    value = binascii.unhexlify(self.data['history'][self.history_idx]['data'])
                    self.history_idx += 1
                    return value
                elif action == 'wait':
                    delay = self.data['history'][self.history_idx]['delay']
                    print(u" => wait for {0}s".format(delay))
                    self.history_idx += 1
                    time.sleep(delay)
                else:
                    print(u"Unkwown action : {0}".format(action))
                    self.history_idx += 1
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
                        value = self.data['loop'][self.loop_idx]['data']
                        print(value)
                        self.loop_idx += 1
                        return value
                    elif action == 'data-hex':
                        value = binascii.unhexlify(self.data['loop'][self.loop_idx]['data'])
                        self.loop_idx += 1
                        return value
                    elif action == 'wait':
                        delay = self.data['loop'][self.loop_idx]['delay']
                        print(u" => wait for {0}s".format(delay))
                        self.loop_idx += 1
                        time.sleep(delay)
                    else:
                        print(u"Unkwown action : {0}".format(action))
                        self.loop_idx += 1
               


if __name__ == "__main__":

    #my_mock = Serial("/media/stock/domotique/git/domogik-plugin-rfxcom/tests/352_data.json")
    my_mock = Serial("/media/stock/domotique/git/domogik-plugin-teleinfo/tests/tests_hphc_data.json")
    while True:
        #my_mock.read()
        my_mock.readline()


