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

Water

Implements
==========

- WaterManager

@author: Fritz <fritz.smh@gmail.com>, BTS Project
@copyright: (C) 2007-2009 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

from domogik.xpl.common.xplmessage import XplMessage
from domogik.xpl.common.plugin import XplPlugin
from domogik.xpl.common.queryconfig import Query
from domogik.xpl.common.xplconnector import Listener
#from domogik.xpl.lib.mirror import Water
#from domogik.xpl.lib.mirror import WaterException
import re


class WaterManager(XplPlugin):
    """ Water management
    """

    def __init__(self):
        """ Init plugin
        """
        XplPlugin.__init__(self, name='water')
        # Get config
        #self._config = Query(self.myxpl, self.log)
        #device = self._config.query('water', device')

        ### Define listener for temperatures
        self.temperatures = {}  # {"device1" : value, "device2" : value2}
        Listener(self.update_temperature_values, self.myxpl, 
                                       {'schema': 'sensor.basic',
                                        'xpltype': 'xpl-stat',
                                        'type': 'temp'})

        ### Define "crontab like" events
      
        # kill legionella
        # TODO : get config param
        cron_expr = '0 0 1 * * *'
        cron_data = re.sub(" +", " ", cron_expr).split(" ")
        self.cron_kill_legionella = TimeCond(cron_data[0], cron_data[1],
                                             cron_data[2], cron_data[3],
                                             cron_data[4], cron_data[5])
        Listener(self.kill_legionella, self.myxpl, {'schema': 'datetime.basic',
                                        'xpltype': 'xpl-trig'})

        # water heating
        # TODO : get config param
        cron_expr = '0 4 * * * *'
        cron_data = re.sub(" +", " ", cron_expr).split(" ")
        self.cron_heat_water = TimeCond(cron_data[0], cron_data[1],
                                        cron_data[2], cron_data[3],
                                        cron_data[4], cron_data[5])
        Listener(self.heat_water, self.myxpl, {'schema': 'datetime.basic',
                                        'xpltype': 'xpl-trig'})

        # consumption analysis
        # TODO : get config param
        cron_expr = '55 23 * * * *'
        cron_data = re.sub(" +", " ", cron_expr).split(" ")
        self.cron_consumption_analysis = TimeCond(cron_data[0], cron_data[1],
                                        cron_data[2], cron_data[3],
                                        cron_data[4], cron_data[5])
        Listener(self.consumption_analysis, self.myxpl, {'schema': 'datetime.basic',
                                        'xpltype': 'xpl-trig'})

        # plugin ready
        self.enable_hbeat()


    def kill_legionella(self, message):
        """ kill legionella instructions

            TODO : explain here what is done (water to 65°, etc)

            @param message : datetime xpl message
        """
        my_date = message.data['format1']
        now = {
               'year' : my_date[0:4],
               'month' : my_date[4:6],
               'day' : my_date[6:8],
               'daynumber' : my_date[14],
               'hour' : my_date[8:10],
               'minute' : my_date[10:12]
              }
        if self.cron_kill_legionella.run(now):
            print("Kill legionella")
            self.log.info("Kill legionella")

            # TODO : instructions to kill legionella
        
    def heat_water(self, message):
        """ water heating instructions

            TODO : explain here what is done 

            @param message : datetime xpl message
        """
        my_date = message.data['format1']
        now = {
               'year' : my_date[0:4],
               'month' : my_date[4:6],
               'day' : my_date[6:8],
               'daynumber' : my_date[14],
               'hour' : my_date[8:10],
               'minute' : my_date[10:12]
              }
        if self.cron_heat_water.run(now):
            print("Heat water")
            self.log.info("Heat water")

            # TODO : instructions to heat water

            # Example for reading a param. Return type : str (string)
            # param name must respect these rules : 
            # - max size : 16
            # - allowed symbols : abcd..z-123..90
            # the_value = self._config.query('water', 'the-param')

            # Example for setting a relay 'ipx-led2' to HIGH :
            # self.set_relay('ipx-led2', 'HIGH')

            # Example for reading a temperature (last known value)
            # the_value = self.get_temperature('device_name')

        
 
    def consumption_analysis(self, message):
        """ water consumption analysis

            TODO : explain here what is done 

            @param message : datetime xpl message
        """
        my_date = message.data['format1']
        now = {
               'year' : my_date[0:4],
               'month' : my_date[4:6],
               'day' : my_date[6:8],
               'daynumber' : my_date[14],
               'hour' : my_date[8:10],
               'minute' : my_date[10:12]
              }
        if self.cron_consumption_analysis.run(now):
            print("Consumption analysis")
            self.log.info("Consumption analysis")

            # TODO : instructions for consumption analysis

            # Example for reading a param. Return type : str (string)
            # param name must respect these rules : 
            # - max size : 16
            # - allowed symbols : abcd..z-123..90
            #the_value = self._config.query('water', 'the-param')
        
            # Example for setting a param.
            #self._config.set('water', 'the-param', 15)


    def set_relay(self, device, value):
        """ Send xpl-trig to give status change
            @param device : device
            @param value : HIGH/LOW
        """
        self.log.info("Send command '%s' on device '%s'" % (value, device))
        msg = XplMessage()
        msg.set_type("xpl-cmnd")
        msg.set_schema('control.basic')
        msg.add_data({'device' :  device})
        msg.add_data({'type' :  'output'})
        msg.add_data({'current' :  value})
        self.myxpl.send(msg)

    def update_temperature_values(self, message):
        """ For each xpl message linked to temperature, get value
            @param message : xpl message
        """
        device = message.data["device"]
        value = message.data["current"]
        self.log.debug("New temperature for '%s' : %s" % (device, value))
        self.temperatures[device] = value

    def get_temperature(self, device):
        """ Read last device known temperature
            @param device : device
        """
        if hasattr(self.temperatures, device):
            value = self.temperatures[device]
        else:
            value = None
        self.log.info("Get temperature for '%s' : %s" % (device, value))
        return value


class TimeCond:
    '''
    Implementation of the time condition
    This allows user to describe time periods like cron
    '''

    def __init__(self, minute, hour, day, month, daynumber, year):
        '''
        Create a time condition
        Each param can be :
        * an integer (eg : 6, 9, 12)
        * a tuple (eg : (3,9)) : repesents an interval (here between 3 and 9)
        * a list (eg : [4,6,9])
        * a list of tuple (eg : [(4,9),(18,22)] : union of intervals
        * a string (eg : '*', '*/8') : '*' = always, '*/X' = every X time unit
        @param year
        @param month
        @param day
        @param daynumber : 0 - 6 for Monday - Sunday
        @param hour
        @param minute
        '''
        self.year = year
        self.month = month
        self.day = day
        self.hour = hour
        self.minute = minute
        self.daynumber = daynumber

    def _check_time(self, timeunit, value):
        '''
            Check the timeunit value
            @param timeunit Can be one of 'year','month','day','daynumber',
                    'hour','minute'
            @param value : the value to check
        '''
        if timeunit not in ['year', 'month', 'day', 'daynumber', 'hour',
                'minute']:
            raise ValueError

        this_unit = eval("self." + timeunit)

        # check particular case of int as a str
        if type(this_unit).__name__ == "str" and this_unit.isdigit():
            this_unit = int(this_unit)

        clas = str(this_unit.__class__).split("'")[1]
        value = clas + "('%s')" % value if clas == "int" or clas == "str" \
                else value
        this_unit = clas + "('%s')" % this_unit if clas == "int" or \
                clas == "str" else this_unit
        call = ("self._check_time_" + clas +"(%s,%s)"% (this_unit, value))
        return eval(call)

    ### Functions to check 'time equality' for each used type

    #Int
    def _check_time_int(self, unit, value):
        '''
        Check time equality between to integers
        @param unit : 'value' of the item in the condition
        @param value : value catched by the system
        '''
        return unit == int(value)

    #tuple : represent an interval
    def _check_time_tuple(self, unit, value):
        '''
        Check if value is in the interval described by the tuple
        @param unit : 'value' of the item in the condition (a tuple)
        @param value : value catched by the system
        '''
        return int(value) in range(unit[0], unit[1] + 1)

    #list
    def _check_time_list(self, unit, value):
        '''
        @param unit can be : a list of int => check if value is in the list
                             a list of tuple => expand each tuple to a list
        @param value : value catched by the system
        '''
        if isinstance(unit[0], tuple):
            return any([_check_time_tuple(u, value) for u in unit])
        else:
            return value in unit

    #string
    def _check_time_str(self, unit, value):
        '''
        @param unit can be  '*' or '*/x'
                            '*' => always true
                            '*/x' => value % x == 0
        @param value : value catched by the system
        '''
        if unit == '*':
            return True
        elif unit.startswith('*/'):
            return (int(value) % int(unit.split('/')[1])) == 0

    ### And of functions for evaluation
    def run(self, statedic):
        # chaque variable peut etre un entier, un interval (tuple), une liste
        # d'intervales ou la chaine '*' ou '*/x'
        return all([self._check_time(t, statedic[t]) for t in [
                'year', 'month', 'day', 'daynumber', 'hour', 'minute']])




if __name__ == "__main__":
    WaterManager()
