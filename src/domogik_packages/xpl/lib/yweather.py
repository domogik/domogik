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

Get Meteo from Yahoo! Weather

Implements
==========

- YWeather

@author: Fritz <fritz.smh@gmail.com>
@copyright: (C) 2007-2012 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

from xml.dom import minidom
import urllib

BASE_URL = "http://weather.yahooapis.com/forecastrss"

# from http://developer.yahoo.com/weather/#codes
CONDITION_CODES = {
    0 : "tornado",
    1 : "tropical storm",
    2 : "hurricane",
    3 : "severe thunderstorms",
    4 : "thunderstorms",
    5 : "mixed rain and snow",
    6 : "mixed rain and sleet",
    7 : "mixed snow and sleet",
    8 : "freezing drizzle",
    9 : "drizzle",
    10 : "freezing rain",
    11 : "showers",
    12 : "showers",
    13 : "snow flurries",
    14 : "light snow showers",
    15 : "blowing snow",
    16 : "snow",
    17 : "hail",
    18 : "sleet",
    19 : "dust",
    20 : "foggy",
    21 : "haze",
    22 : "smoky",
    23 : "blustery",
    24 : "windy",
    25 : "cold",
    26 : "cloudy",
    27 : "mostly cloudy (night)",
    28 : "mostly cloudy (day)",
    29 : "partly cloudy (night)",
    30 : "partly cloudy (day)",
    31 : "clear (night)",
    32 : "sunny",
    33 : "fair (night)",
    34 : "fair (day)",
    35 : "mixed rain and hail",
    36 : "hot",
    37 : "isolated thunderstorms",
    38 : "scattered thunderstorms",
    39 : "scattered thunderstorms",
    40 : "scattered showers",
    41 : "heavy snow",
    42 : "scattered snow showers",
    43 : "heavy snow",
    44 : "partly cloudy",
    45 : "thundershowers",
    46 : "snow showers",
    47 : "isolated thundershowers",
    3200 : "not available"
    }

class YWeatherException(Exception):  
    """                                                                         
    Yahoo Weather exception
    """                                                                         
                                                                                
    def __init__(self, value):                                                  
        Exception.__init__(self)
        self.value = value                                                      
                                                                                
    def __str__(self):                                                          
        return repr(self.value)           
        
        
class YWeather:
    """ YWeather informations
    """

    def __init__(self, log, callback):
        """ Init YWeather object
            @param log : log instance
            @param callback : callback
        """
        self._log = log
        self._callback = callback
        self._url = None

    def open(self, town, unit, device):
        """ Define Yahoo weather web service url
            @param url : web service url
            @param device : address set by user in config page
        """
        self._url = "%s?w=%s&u=%s" % (BASE_URL, town, unit)
        self._device = device
        #TODO : add some check (town, etc)
            
    def close(self):
        """ close YWeather service
        """
        # nothing to do here
        pass
   
    def listen(self, interval):
        """ Loop for calling web service
            @param interval : time between each call to webs ervice
        """
        # TODO : delete ?
        pass


    def get(self):
        """ Call read() and send result to callback
        """
        self._callback(self._device, self.read())

            
    def read(self):        
        """ Get data from web service
        """        
        weather = {}
        # get xml data
        self._log.info("Call url : %s" % self._url)
        resp = urllib.urlopen(self._url)
        xml_data = resp.read()
        my_xml = minidom.parseString(xml_data)

        # get update time
        update_time = my_xml.getElementsByTagName("lastBuildDate")[0].firstChild.nodeValue

        # get location data
        location = {}
        my_loc = my_xml.getElementsByTagName("yweather:location")[0]
        location["city"] =  my_loc.getAttribute("city")
        location["region"] =  my_loc.getAttribute("region")
        location["country"] =  my_loc.getAttribute("country")

        # get units
        units = {}
        my_uni = my_xml.getElementsByTagName("yweather:units")[0]
        units["temperature"] = my_uni.getAttribute("temperature")
        units["distance"] = my_uni.getAttribute("distance")
        units["pressure"] = my_uni.getAttribute("pressure")
        units["speed"] = my_uni.getAttribute("speed")

        # get wind
        wind = {}
        my_win = my_xml.getElementsByTagName("yweather:wind")[0]
        wind["chill"] = my_win.getAttribute("chill")
        wind["direction"] = my_win.getAttribute("direction")
        wind["speed"] = my_win.getAttribute("speed")

        # get atmosphere
        atmos = {}
        my_atm = my_xml.getElementsByTagName("yweather:atmosphere")[0]
        atmos["humidity"] = my_atm.getAttribute("humidity")
        atmos["visibility"] = my_atm.getAttribute("visibility")
        atmos["pressure"] = my_atm.getAttribute("pressure")
        atmos["rising"] = my_atm.getAttribute("rising")

        # get astronomy
        astro = {}
        my_ast = my_xml.getElementsByTagName("yweather:astronomy")[0]
        astro["sunrise"] = my_ast.getAttribute("sunrise")
        astro["sunset"] = my_ast.getAttribute("sunset")

        # get picture url
        # note : this data should not be used but in case...
        picture = my_xml.getElementsByTagName("image")[0].getElementsByTagName("url")[0].firstChild.nodeValue

        # get <item> elt for following data
        item = my_xml.getElementsByTagName("item")[0]

        # get geography
        geo = {}
        geo["latitude"] = item.getElementsByTagName("geo:lat")[0].firstChild.nodeValue
        geo["longitude"] = item.getElementsByTagName("geo:long")[0].firstChild.nodeValue

        # get current condition
        current = {}
        my_cnd = my_xml.getElementsByTagName("yweather:condition")[0]
        current["text"] = my_cnd.getAttribute("text")
        current["code"] = my_cnd.getAttribute("code")
        current["temperature"] = my_cnd.getAttribute("temp")

        # get today conditions
        today = {}
        my_cnd = my_xml.getElementsByTagName("yweather:forecast")[0]
        today["text"] = my_cnd.getAttribute("text")
        today["code"] = my_cnd.getAttribute("code")
        today["temperature_high"] = my_cnd.getAttribute("high")
        today["temperature_low"] = my_cnd.getAttribute("low")

        # get tomorrow conditions
        tomorrow = {}
        my_cnd = my_xml.getElementsByTagName("yweather:forecast")[1]
        tomorrow["text"] = my_cnd.getAttribute("text")
        tomorrow["code"] = my_cnd.getAttribute("code")
        tomorrow["temperature_high"] = my_cnd.getAttribute("temperature_high")
        tomorrow["temperature_low"] = my_cnd.getAttribute("temperature_low")

        # Generate weather item
        weather["update_time"] = update_time
        weather["location"] = location
        weather["units"] = units
        weather["wind"] = wind
        weather["atmosphere"] = atmos
        weather["astronomy"] = astro
        weather["picture"] = picture
        weather["geography"] = geo
        weather["current"] = current
        weather["today"] = today
        weather["tomorrow"] = tomorrow
        return weather
                    

class Log:
    def __init__(self):
        pass
    
    def debug(self, msg):
        print("DEBUG : %s" % msg)
    
    def error(self, msg):
        print("ERROR : %s" % msg)
    
    def warning(self, msg):
        print("WARN : %s" % msg)
    
    def info(self, msg):
        print("INFO : %s" % msg)



if __name__ == "__main__":
    l = Log()
    yw = YWeather(l, None)
    yw.open(613858, "c")
    print(yw.read())
