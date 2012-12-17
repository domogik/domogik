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

Send demo data over xPL

Implements
==========

@author: Fritz <fritz.smh@gmail.com>
@copyright: (C) 2007-2012 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

from json import load
from urllib2 import urlopen
from pprint import pprint
import datetime
import math

# for DemoUi
import BaseHTTPServer
import os
import mimetypes
import shutil

#JQUERY = "jquery-1.8.2.min.js"
#JQUERY_UI = "jquery-ui-1.9.1.min.js"
#JQUERY_CSS = "jquery-ui.css"



class DemoData():

    def __init__(self, log, cb_send_sensor_basic, cb_send_teleinfo_basic):
        self.log = log
        self.cb_send_sensor_basic = cb_send_sensor_basic
        self.cb_send_teleinfo_basic = cb_send_teleinfo_basic
        pass

    # thermometer => temperature
    # humidity
    # pressure
    def weather_data(self):
        try:
            data = urlopen('http://openweathermap.org/data/2.1/find/name?q=paris&lang=fr')
            cities = load(data)
            if cities['count'] > 0:
                city = cities['list'][0]
                #pprint(city['main'])
                #pprint(city['weather'])
    
                # temperature in celcius
                #g(x)=(5/9)x-160/9 	  
                #temp = ((5./9.)*(city['main']['temp'])-160./9.)/10
                temp = (city['main']['temp'] - 273.15)
                self.cb_send_sensor_basic("demo_temperature", "temp", temp)
                # humidity
                self.cb_send_sensor_basic("demo_humidity", "humidity", city['main']['humidity'])
                #pressure
                self.cb_send_sensor_basic("demo_pressure", "pressure", city['main']['pressure'])
        except:
            self.log.error("Error while getting weather data")

    def teleinfo_data(self):
        try:
            # Demo trame :
            #adco=030928084432
            #optarif=hc..
            #isousc=45
            #hchc=016796635
            #hchp=020697453
            #ptec=hp..
            #iinst=001
            #imax=048
            #papp=00310
            #hhphc=d
            #motdetat=000000
            #device=teleinfo
    
            teleinfo = {}
    
            # static data
            teleinfo['adco'] = '012345678901'
            teleinfo['optarif'] = 'hc..'
            teleinfo['isousc'] = '45'
            teleinfo['imax'] = '048'
            teleinfo['motdetat'] = '000000'
            teleinfo['device'] = 'demo_teleinfo'
    
            # the electric counter starts on the 1st of november 2012
            # we assume that HC are from 22h to 6h
            # each hour we will set exactly tha same papp all the hour
            # the base papp is 300
            # each 2 hour, we add 300 
            # from 2h to 6h, we heat the water : we add 2100
            # dynamic data
            # iinst = papp / 230
            day_0 = datetime.datetime(2012, 11, 1)
            now = datetime.datetime.now()
            nb_days = self._get_number_of_days(day_0, now)
            hour = (now - now.replace(hour=0,minute=0,second=0)).seconds / 3600
            papp_hc = {}
            papp_hp = {}
            papp = {}
            papp_hc[0] = 300 
            papp_hc[1] = 600
            papp_hc[2] = 2400
            papp_hc[3] = 2700
            papp_hc[4] = 2400
            papp_hc[5] = 2700
            papp_hc[6] = 0
            papp_hc[7] = 0
            papp_hc[8] = 0
            papp_hc[9] = 0
            papp_hc[10] = 0
            papp_hc[11] = 0
            papp_hc[12] = 0
            papp_hc[13] = 0
            papp_hc[14] = 0
            papp_hc[15] = 0
            papp_hc[16] = 0
            papp_hc[17] = 0
            papp_hc[18] = 0
            papp_hc[19] = 0
            papp_hc[20] = 0
            papp_hc[21] = 0
            papp_hc[22] = 300
            papp_hc[23] = 600
            papp_hp[0] = 0
            papp_hp[1] = 0
            papp_hp[2] = 0
            papp_hp[3] = 0
            papp_hp[4] = 0
            papp_hp[5] = 0
            papp_hp[6] = 300
            papp_hp[7] = 600
            papp_hp[8] = 300
            papp_hp[9] = 600
            papp_hp[10] = 300
            papp_hp[11] = 600
            papp_hp[12] = 300
            papp_hp[13] = 600
            papp_hp[14] = 300
            papp_hp[15] = 600
            papp_hp[16] = 300
            papp_hp[17] = 600
            papp_hp[18] = 300
            papp_hp[19] = 600
            papp_hp[20] = 300
            papp_hp[21] = 600
            papp_hp[22] = 0
            papp_hp[23] = 0
    
            # get hch* for a full day
            hchc_fullday = 0
            hchp_fullday = 0
            for idx in range(0, 23):
                hchc_fullday += papp_hc[idx]
                hchp_fullday += papp_hp[idx]
                papp[idx] = papp_hc[idx] + papp_hp[idx]
    
            # get hch* for all days since the 1st nov 2012
            hchc_alldays = nb_days * hchc_fullday
            hchp_alldays = nb_days * hchp_fullday
    
            # get hch* for the current hour
            hchc = hchc_alldays
            hchp = hchp_alldays
            for idx in range(0, hour):
                hchc += papp_hc[idx]
                hchp += papp_hp[idx]
    
    
    
            teleinfo['hchc'] = "%09d" % hchc
            teleinfo['hchp'] = "%09d" % hchp
            if 0 <= hour < 6 or 22 <= hour <= 23:
                teleinfo['ptec'] = 'hc..'
            else:
                teleinfo['ptec'] = 'hp..'
            teleinfo['iinst'] = "%03d" % (papp[hour] / 230)
            teleinfo['papp'] = "%05d" % papp[hour]
            teleinfo['hhphc'] = 'd'
            #print teleinfo
            self.cb_send_teleinfo_basic(teleinfo)
        except:
            self.log.error("Error while creating teleinfo data")
      
    # tank
    # level and distance 
    def tank_data(self):
        try:
            now = datetime.datetime.now()
            minute = (now - now.replace(hour=0,minute=0,second=0)).seconds / 60
            minute += 0.0  # to make minutes as a float
            # factor to expand 2pi to 1440 minutes
            factor = 720/math.pi       

            level = (math.cos(minute/factor)+1)*50  # level in %
            print "level=%s, minute=%s, factor=%s" % (level, minute, factor)
            #level
            self.cb_send_sensor_basic("demo_tank", "percent", level)
            #distance : we assume distance = 100-level (a 1m tank)
            self.cb_send_sensor_basic("demo_tank", "distance", 100-level)
        except:
            self.log.error("Error while creating tank data")


    def _get_number_of_days(self, date_from, date_to):
        """Returns a float equals to the timedelta between two dates given as string."""

        timedelta = date_to - date_from
        diff_day = timedelta.days 
        return diff_day


class UIHandler( BaseHTTPServer.BaseHTTPRequestHandler ):

    server_version= "DemoUI/1.1"

    # display the pages
    def do_GET( self ):
        self.log_message( "Command: %s Path: %s Headers: %r"
                          % ( self.command, self.path, self.headers.items() ) )

        # split path and args
        buf = self.path.split("?")
        path = buf[0]
        path_elts = path.split("/")
        print path_elts
        # manage pages
        if path == "/":
            self._display_home()
        elif path_elts[1] == "js":
            self._get_file(path)
        elif path_elts[1] == "css":
            self._get_file(path)
        elif path_elts[1] == "img":
            self._get_file(path)
        elif path_elts[1] == "webcam.jpg":
            self._display_webcam()
        else:
            self._send_http_response(404)

    # actions
    def do_POST( self ):
        self.log_message( "Command: %s Path: %s Headers: %r"
                          % ( self.command, self.path, self.headers.items() ) )
        # split path and args
        buf = self.path.split("?")
        path = buf[0]
        if len(buf) == 2:
            args = buf[1].split("&")

        # get args
        if self.headers.has_key("content-length"):
            post_length = int(self.headers['content-length'])
            post_data = self.rfile.read(post_length)
            post_tab = post_data.split("&")
            args = {}
            for arg in post_tab:
                tmp_arg = arg.split("=")
                args[tmp_arg[0]] = tmp_arg[1]

        # manage actions
        if path == "/rgb":
            self.server.handler_params[0].send_arduino_rgb('demo_rgb_led', 'setcolor', args['color'])
            self._send_http_response(200)
        elif path == "/switch":
            self.server.handler_params[0].send_lighting_device('demo_switch', 'goto', args['level'])
            self._send_http_response(200)
        elif path == "/dimmer":
            self.server.handler_params[0].send_lighting_device('demo_dimmer', 'goto', args['level'])
            self._send_http_response(200)
        elif path == "/caller_id":
            self.server.handler_params[0].send_cid_basic('demo_cid', 'inbound', args['phone'])
            self._send_http_response(200)
        else:
            self._send_http_response(404)

    def _send_http_response(self, number):
        """ Send a xxx error
        """
        try:
            self.send_response(number)
            self.send_header("Content-Type","text/html")
            self.end_headers()
            self.wfile.write("%s - Not found" % number)
        except IOError as err:
            if err.errno == errno.EPIPE:
                # [Errno 32] Broken pipe : client closed connexion
                pass
            else:
                raise err
 
    def dumpReq( self, formInput=None ):
        response= "<html><head></head><body>"
        response+= "<p>HTTP Request</p>"
        response+= "<p>self.command= <tt>%s</tt></p>" % ( self.command )
        response+= "<p>self.path= <tt>%s</tt></p>" % ( self.path )
        response+= "</body></html>"
        self.sendPage( "text/html", response )

    def sendPage( self, type, body ):
        self.send_response( 200 )
        self.send_header( "Content-type", type )
        self.send_header( "Content-length", str(len(body)) )
        self.end_headers()
        self.wfile.write( body )

    def _get_file(self, filename):
        # get the resources folder
        res_dir = self.server.handler_params[0].get_data_files_directory()
        the_file = "%s/%s" % (res_dir, filename)
        self._download_file(the_file)

    def _display_home(self):
        # get the resources folder
        res_dir = self.server.handler_params[0].get_data_files_directory()
        home_file = "%s/index.html" % res_dir
        print home_file
        self._download_file(home_file)

    def _display_webcam(self):
        # get the resources folder
        res_dir = self.server.handler_params[0].get_data_files_directory()
        num = 0
        now = datetime.datetime.now()
        second = (now - now.replace(hour=0,minute=0,second=0)).seconds
        num = second % 10
        cam_file = "%s/webcam/webcam-%s.jpg" % (res_dir, num)
        print cam_file
        self._download_file(cam_file)

    def _download_file(self, file_name):
        """ Download a file
        """
        # Check file opening
        try:
            my_file = open("%s" % (file_name), "rb")
        except IOError:
            self._send_http_response(404)
            return

        # Get informations on file
        ctype = None
        file_stat = os.fstat(my_file.fileno())
        #last_modified = os.stat("%s" % (file_name))[stat.ST_MTIME]
        last_modified = os.path.getmtime(file_name)

        # Get mimetype information
        if not mimetypes.inited:
            mimetypes.init()
        extension_map = mimetypes.types_map.copy()
        extension_map.update({
                '' : 'application/octet-stream', # default
                '.py' : 'text/plain'})
        basename, extension = os.path.splitext(file_name)
        if extension in extension_map:
            ctype = extension_map[extension]
        else:
            extension = extension.lower()
            if extension in extension_map:
                ctype = extension_map[extension]
            else:
                ctype = extension_map['']
    
        # Send file
        self.send_response(200)
        self.send_header("Content-type", ctype)
        self.send_header("Content-Length", str(file_stat[6]))
        self.send_header("Last-Modified", last_modified)
        self.end_headers()
        shutil.copyfileobj(my_file, self.wfile)
        my_file.close()



class DummyLog:

    def info(self, text):
        print("INFO %s" % text)

    def warn(self, text):
        print("WARN %s" % text)

    def debug(self, text):
        print("DEBUG %s" % text)

    def error(self, text):
        print("ERROR %s" % text)

def dummy_send_sensor_basic(device, type, current):
    print("%s / %s / %s" % (device, type, current))
    
if __name__ == "__main__":
    Log = DummyLog()
    DDL = DemoData(Log, dummy_send_sensor_basic)
    DDL.weather_data()
    DDL.teleinfo_data()
