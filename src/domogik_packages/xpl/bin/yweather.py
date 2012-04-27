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

Get weather informations from Yahoo! Weather

Implements
==========

- YWeatherManager

@author: Fritz <fritz.smh@gmail.com>
@copyright: (C) 2007-2009 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

from domogik.xpl.common.xplconnector import XplTimer
from domogik.xpl.common.xplmessage import XplMessage
from domogik.xpl.common.plugin import XplPlugin
from domogik.xpl.common.queryconfig import Query
from domogik_packages.xpl.lib.yweather import YWeather
from domogik_packages.xpl.lib.yweather import YWeatherException
import threading
import datetime

TIME_BETWEEN_EACH_WEATHER_READ = 30*60 # 30 minutes

class YWeatherManager(XplPlugin):
    """ Get data from Yahoo weather and send them on xPL
    """

    def __init__(self):
        """ Init plugin
        """
        XplPlugin.__init__(self, name='yweather')

        # Get config
        self._config = Query(self.myxpl, self.log)
        unit = self._config.query('yweather', 'unit' )
        if unit == None:
            self.log.error("Unit not configured : exiting")
            print("Unit not configured : exiting")
            self.force_leave()
            return
        unit = unit.lower()
        
        self.enable_current = self._config.query('yweather', 'en-current' )
        self.enable_previsionnal = self._config.query('yweather', 'en-prev' )

        self.cities = {}
        num = 1
        loop = True
        while loop == True:
            city_code = self._config.query('yweather', 'city-%s' % str(num))
            device = self._config.query('yweather', 'device-%s' % str(num))
            if city_code != None:
                self.cities[city_code] = { "device" : device }
                num = num + 1
            else:
                loop = False

        # Open weather for cities
        for city in self.cities:
            self.cities[city]["obj"] = YWeather(self.log, self.send_xpl)
            try:
                self.log.info("Init weather for '%s'" % city)
                self.cities[city]["obj"].open(city, unit,
                                              self.cities[city]["device"])
            except YWeatherException as err:
                self.log.error(err.value)
                print(err.value)
                self.force_leave()
                return

        # Start listening for weather
        for city in self.cities:
            try:
                self.log.info("Start listening weather for '%s'" % city)
                self._listen_thr = XplTimer(TIME_BETWEEN_EACH_WEATHER_READ, \
                                            self.cities[city]["obj"].get, \
                                            self.myxpl)
                self._listen_thr.start()
                self.enable_hbeat()
            except YWeatherException as err:
                self.log.error(err.value)
                print(err.value)
                self.force_leave()
                return
        self.enable_hbeat()



    def send_xpl(self, device, weather):
        """ Send xPL message on network
            @param device : device (address set by user in config page)
            @param weather : weather data
        """
        # current part (sensor.basic)
        if self.enable_current == 'True':
            self._send_current(device, weather, 
                               "current", "temperature", "temp",
                               units = weather["units"]["temperature"])
            self._send_current(device, weather, 
                               "atmosphere", "pressure", "pressure",
                               units = weather["units"]["pressure"])
            self._send_current(device, weather, 
                               "atmosphere", "humidity", "humidity",
                               units = "%")
            self._send_current(device, weather, 
                               "atmosphere", "visibility", "visibility",
                               units = weather["units"]["distance"])
            self._send_current(device, weather, 
                               "atmosphere", "rising", "rising")
            self._send_current(device, weather, 
                               "wind", "chill", "chill")
            self._send_current(device, weather, 
                               "wind", "direction", "direction")
            self._send_current(device, weather, 
                               "wind", "speed", "speed",
                               units = weather["units"]["speed"])
            self._send_current(device, weather, 
                               "current", "code", "condition-code")
            self._send_current(device, weather, 
                               "current", "text", "condition-text")


        # previsionnal part
        if self.enable_previsionnal == 'True':
            common = {
                      "city" : weather["location"]["city"],
                      "region" : weather["location"]["region"],
                      "country" : weather["location"]["country"],
                      "unit-distance" : weather["units"]["distance"],
                      "unit-pressure" : weather["units"]["pressure"],
                      "unit-speed" : weather["units"]["speed"],
                      "unit-temperature" : weather["units"]["temperature"]
                     }

            my_today = datetime.date.today().isoformat() 
            today = {
                   "day" : my_today,
                   "condition-code" : weather["today"]["code"],
                   "condition-text" : weather["today"]["text"],
                   "temperature-low" : weather["today"]["temperature_low"],
                   "temperature-high" : weather["today"]["temperature_high"],
                     }

            my_tomorrow = (datetime.date.today() + \
                           datetime.timedelta(days = 1)).isoformat()
            tomorrow = {
                   "day" : my_tomorrow,
                   "condition-code" : weather["tomorrow"]["code"],
                   "condition-text" : weather["tomorrow"]["text"],
                   "temperature-low" : weather["tomorrow"]["temperature_low"],
                   "temperature-high" : weather["tomorrow"]["temperature_high"],
                     }

            today.update(common)
            tomorrow.update(common)
            self._send_previsionnal(device, today)
            self._send_previsionnal(device, tomorrow)


    def _send_current(self, device, weather, category, key, xpl_type, 
                      units = None):
        """ Check if data exists and sent it over xpl
            @param device : device (address set by user in config page)
            @param weather : weather struc
            @param category : category of data (atmosphere, today, tomorrow...)
            @param key : key in category
            @param xpl_type : type to use in xpl schema
            @param units : unit for value
        """
        try:
            self._send_sensor_basic(device = device,
                                            type = xpl_type,
                                            current = weather[category][key],
                                            units = units)
        except KeyError:
            # no data : pass
            print("No data for %s>%s" % (category, key))
            pass


    def _send_sensor_basic(self, device, type, current, units = None):
        """ Send sensor.basic xPL schema
            @param device : device
            @param type : type
            @param current : current
        """
        print("D=%s, T=%s, C=%s" % (device, type, current))
        if current == "":
            return
        msg = XplMessage()
        msg.set_type("xpl-stat")
        msg.set_schema("sensor.basic")
        msg.add_data({"device" : device})
        msg.add_data({"type" : type})
        msg.add_data({"current" : current})
        if units != None:
            msg.add_data({"units" : units})
        self.myxpl.send(msg)


    def _send_previsionnal(self, device, data):
        """ Send weather.basic xPL schema
            @param device : device
            @param data : dictionnary of data to send
        """
        print("D=%s, %s" % (device, data))
        msg = XplMessage()
        msg.set_type("xpl-stat")
        msg.set_schema("weather.basic")
        msg.add_data({"device" : device})
        for key in data:
            if data[key] != "":
                msg.add_data({key : data[key]})

        self.myxpl.send(msg)


if __name__ == "__main__":
    YWeatherManager()
