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

    def __init__(self, device, baudrate = None, parity = None, stopbits = None):
        """ Construtor
            @param device : useless, just for compatibility
            @param baudrate : useless, just for compatibility
            @param parity : useless, just for compatibility
            @param stopbits : useless, just for compatibility
        """
        # there is nothing to do, excepting logging!
        print(u"Fake serial device created for device '{0}'".format(device))
        
        # read index
        self.read_idx = 0

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
        fake_data = [
                       { 'action' : 'data', 
                         'data' : '61'
                       },
                       { 'action' : 'data', 
                         'data' : '0d'
                       },
                       { 'action' : 'data', 
                         'data' : '010001025344000c2f00000000'
                       },
                       { 'action' : 'wait', 
                         'delay' : 10
                       },
                       { 'action' : 'data', 
                         'data' : '0a'
                       },
                       { 'action' : 'data', 
                         'data' : '520100250400d4470350'
                       },
                       { 'action' : 'wait', 
                         'delay' : 15
                       },
                       { 'action' : 'data', 
                         'data' : '0a'
                       },
                       { 'action' : 'data', 
                         'data' : '520100250400d4470350'
                       },
                       { 'action' : 'wait', 
                         'delay' : 15
                       },
                       { 'action' : 'data', 
                         'data' : '0a'
                       },
                       { 'action' : 'data', 
                         'data' : '520100250400d4470350'
                       },
                       { 'action' : 'wait', 
                         'delay' : 15
                       },
                       { 'action' : 'data', 
                         'data' : '0a'
                       },
                       { 'action' : 'data', 
                         'data' : '520100250400d4470350'
                       },
                   ]
        while True:
            print "%s vs %s" % (self.read_idx, len(fake_data))
            if self.read_idx < len(fake_data)-1:
                self.read_idx += 1
                action = fake_data[self.read_idx]['action']
                print(u"Action = {0}".format(action))
                if action == 'data':
                    value = binascii.unhexlify(fake_data[self.read_idx]['data'])
                    print value
                    #print(u" => read {0}".format(value))
                    return value
                if action == 'wait':
                    delay = fake_data[self.read_idx]['delay']
                    print(u" => wait for {0}s".format(delay))
                    time.sleep(delay)
            else:
                raise SerialException(u"There is nothing else to read in the fake serial device")
               


if __name__ == "__main__":

    my_mock = Serial("/dev/rfxcom")
    my_mock.read()
    my_mock.read()
    my_mock.read()
    my_mock.read()
    my_mock.read()
    my_mock.read()
    my_mock.read()
    my_mock.read()


# TODO :
# plugins : add an option to the MQ to send options to the plugin from the manager to load a lib and give a scenario name
# add a way to eternally do some actions (repeat the last 2 ?)
