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

Module purpose
==============

Main class for the xbmc Domogik interface

Implements
==========

- MyEffect
- LeftMenu
- DeviceRepresentation
- DeviceSet
- Window

@author: Maxence Dunnewind <maxence@dunnewind.net>
@copyright: (C) 2007-2009 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

import time 


import os
import math
from time import sleep

import sys 
print "PAAAATH : %s" % sys.path
from domogik.common.database import *

import xbmc
import xbmcgui

#get actioncodes from keymap.xml

ACTION_MOVE_LEFT                             = 1    
ACTION_MOVE_RIGHT                            = 2
ACTION_MOVE_UP                                = 3
ACTION_MOVE_DOWN                            = 4
ACTION_PAGE_UP                                = 5
ACTION_PAGE_DOWN                            = 6
ACTION_SELECT_ITEM                        = 7
ACTION_HIGHLIGHT_ITEM                    = 8
ACTION_PARENT_DIR                            = 9
ACTION_PREVIOUS_MENU                    = 10
ACTION_SHOW_INFO                            = 11

ACTION_PAUSE                                    = 12
ACTION_STOP                                        = 13
ACTION_NEXT_ITEM                            = 14
ACTION_PREV_ITEM                            = 15

#
# This helper is used to read entries from the database
#
DB = DbHelper()

class MyEffect:
    """
    Custom effects
    """
    def __init__(self, window):
        self.window = window

    def fademove(self, items, hz, vl):
        """
        fade move of hz px in horizontal and vl in vertical
        """
        if hz == 0 and vl == 0:
            return
        cur_x = {}
        cur_y = {}
        for item in items:
            cur_x[repr(item)] = item.getPosition()[0]
            cur_y[repr(item)] = item.getPosition()[1]
        old_x = cur_x.copy()
        old_y = cur_y.copy()
        nb_step = max(abs(hz), abs(vl)) / 4.0 
        h_step = hz / nb_step
        v_step = vl / nb_step
        for i in range(int(nb_step)):
            for item in items:
                cur_x[repr(item)] = cur_x[repr(item)] + h_step
                cur_y[repr(item)] = cur_y[repr(item)] + v_step
                item.setPosition(cur_x[repr(item)], cur_y[repr(item)])
            sleep(.01)
        for item in items:
            #Take care of the round made by int()
            item.setPosition(old_x[repr(item)] + hz, old_y[repr(item)] + vl)
    
class LeftMenu:
    """
    Define the left menu
    """

    def __init__(self, window, leftpad, toppad):
#        @param window : The main window against which we should register our items 
#        @param leftpad : The Leftmenu will top-left corner padding from left side
#        @param leftpad : The Leftmenu will top-left corner padding from top
        self.menu = xbmcgui.ControlList(10,100,150,300)
        window.addControl(self.menu)
        for room in DB.list_rooms():
            self.menu.addItem(room.name)
#        self.menu.addItem('Maison')
#        self.menu.addItem('Chambre 1')
#        self.menu.addItem('Chambre 2')
#        self.menu.addItem('Salle d\'eau')
#        self.menu.addItem('Garage')
#        self.button = xbmcgui.ControlButton(10, 310, 90, 30, "Button")
        #window.addControl(self.button)
#        self.strAction = xbmcgui.ControlLabel(50, 100, 100, 20, 'action', 'font13', '0xFFFF3300')
#        self.strButton = xbmcgui.ControlLabel(50, 150, 100, 20, 'button', 'font13', '0xFFFFFFFF')
 #       window.addControl(self.strAction)
 #       window.addControl(self.strButton)
        
class DeviceRepresentation:
    """
    Representation of a device
    """
    UNITS = {'light':'',
            'temperature':u'°C'}

    def __init__(self, window, line, type, technology, id, name, value, left, top):
        #@param window : The main window against which we should register our items 
        #@param line : the line where the device is
        #@param type : device type (light, temperature, etc)
        #@param name : device name 
        #@param value : device value
        #@param left : left padding of the left-top corner
        #@param top : top padding of the left-top corner
        self._id = id 
        self._technology = technology 
        self.n = name
        self.line = line
        self.image = xbmcgui.ControlImage(left + 10, top + 10, 80, 80, os.path.realpath('.') + '/light.png')
        self._win = window
        self.name = xbmcgui.ControlButton(left + 10, top + 85, 80, 20, name, focusedColor = '0xF0F0F0F0', alignment = 2)
#        self.name.setAnimations([('unfocus', 'effect=rotate start=0 end=180 time=4000',)])
        window.addControl(self.image)
        window.addControl(self.name)
        self.image.setAnimations([('WindowOpen', 'effect=slide start=500 time=800')]) 
        self.name.setAnimations([('Focus', 'effect=fade start=60 end=100 time=200'), ('UnFocus', 'effect=fade start=100 end=60 time=200')]) 

    def __del__(self):
        self._win.removeControl(self.image)
        self._win.removeControl(self.name)

class DeviceSet:
    """
    Set of device to create
    """
    def __init__(self, window, focus, left, top, nb_device_per_line, devices):
        #@param window : The main window against which we should register our items 
        #@param left : left padding of the left-top corner
        #@param top : top padding of the left-top corner
        #@param nb_device_per_line : Max device to set on one line
        #@param devices : list of tuple (type, technology, id, name, value)
        self.devices = []
        self._visible_lines = int(((window.getHeight() - top) / (110 * window.ratio )))
        self._nb_device_per_line = nb_device_per_line
        self._eff = MyEffect(window)
        self._top = top
        self._win = window
        for j in range(math.ceil(len(devices) / (nb_device_per_line * 1.0))):
            for i in range(nb_device_per_line):
                if (j * nb_device_per_line + i) >= len(devices):
                    break
                dev_t = devices[j * nb_device_per_line + i]
                dev = DeviceRepresentation(window, j, dev_t[0], dev_t[1], dev_t[2],
                        dev_t[3], dev_t[4], left + i * 110, top + j * 110)
                self.devices.append(dev)

        #Update controls
        for i in range(len(devices)):
            #Left and Right
            if (i == len(devices) - 1):
                self.devices[0].name.controlLeft(self.devices[len(devices) - 1].name)
                self.devices[len(devices) - 1].name.controlRight(self.devices[0].name)
            else:
                self.devices[i+1].name.controlLeft(self.devices[i].name)
                self.devices[i].name.controlRight(self.devices[i+1].name)
            #Down
            if (i + nb_device_per_line < len(devices)):
                self.devices[i].name.controlDown(self.devices[i + nb_device_per_line].name)
            else:
                self.devices[i].name.controlDown(self.devices[i % nb_device_per_line].name)
            #Up
            if (i - nb_device_per_line >= 0):
                #Il y a une ligne au dessus
                self.devices[i].name.controlUp(self.devices[i - nb_device_per_line].name)
            elif ((len(devices) % nb_device_per_line) > i):
                #Il y a un element sur la meme colonne, derniere ligne
                print "device : %s" % (len(devices) - (len(devices)  % nb_device_per_line) + i)
                self.devices[i].name.controlUp(self.devices[(len(devices) - (len(devices)  % nb_device_per_line) + i)].name)
            else:
                #avant derniere ligne
                self.devices[i].name.controlUp(self.devices[(len(devices) - (len(devices)  % nb_device_per_line) + i - nb_device_per_line)].name)

        window.setFocus(self.devices[nb_device_per_line].name)
        self._oldline = None

    def get_line_of_device(self, device):
        """
        Return the line of the device
        """
        for d in self.devices:
            if d.name == device:
                return d.line

    def push_up(self):
        """
        scroll the device list for 1 line up 
        """
        self._eff.fademove(self.get_all_subitems(), 0, -110)

    def push_down(self):
        """
        scroll the device list for 1 line down 
        """
        self._eff.fademove(self.get_all_subitems(), 0, 110)

    def center_line_of_device(self, device):
        """
        put the line a device 'device' on center
        """
        print "Device is : %s" % device
        line = self.get_line_of_device(device)
        print "line is : %s" % line
        wanted_position = (self._win.getHeight()) / 2 + self._top - 55
        real_position = device.getPosition()[1]
        print "Wanted position is : %s" % wanted_position
        print "real position is : %s" % real_position
        padding = wanted_position - real_position
        print "padding is : %s" % padding
        print "oldine is : %s" % self._oldline  
        if line == 0 and (self._oldline ==  len(self.devices) / self._nb_device_per_line) and self._oldline >= self._visible_lines:
            #avoid a bug if we loop from last line to first on2e
            #need to compute padding ourself since getPosition is wrong
            padding = ((len(self.devices) % self._nb_device_per_line) + self._visible_lines / 2 + 1) * 110 
            self._eff.fademove(self.get_all_subitems(), 0, padding)
            #Now it's on the screen, we can move it normally
            self._oldline = line
            #Nasty way to get it on the right position
#            self.center_line_of_device(device)
        else:
            self._eff.fademove(self.get_all_subitems(), 0, padding)
            self._oldline = line

    def get_all_subitems(self):
        """
        Return all items name + image of the deviceset
        """
        r = [i.name for i in self.devices]
        r.extend([i.image for i in self.devices])
        return r

    def __del__(self):
        """
        Delete all DeviceRepresentation
        """
        print "DELETE DEVICES" #do *not* remove this debug
        for device in self._devices:
            del device

class DMGWindow(xbmcgui.Window):
    def __init__(self):
    
        self.addControl(xbmcgui.ControlImage(0,0,720,576, 'background.png'))
        self.compute_ratio()
        self.left = LeftMenu(self, 0, 0)    
        self.eff = MyEffect(self)

        self._set = None
        self.update_center()


    def compute_ratio(self):
        resolution = self.getResolution()
        ratio = 0
        if resolution == 0:
            ratio = 1080
        elif resolution == 1:
            ratio = 720
        elif resolution == 6 or resolution == 7:
            ratio = 576
        else:
            ratio = 480
        self.ratio = float(self.getHeight()) / float(ratio)

    def onAction(self, action):
#        print "FOCUS ON : %s" % self.getFocus()
        if action == ACTION_PREVIOUS_MENU:
            print('action recieved: previous')
            self.close()
        elif (action in [ACTION_MOVE_UP, ACTION_MOVE_DOWN, ACTION_MOVE_LEFT, ACTION_MOVE_RIGHT]) and isinstance(self.getFocus(), xbmcgui.ControlButton) :
            self._set.center_line_of_device(self.getFocus())
                
        if action == ACTION_PAUSE:
            self.setFocus(self.left.menu)

    def onControl(self, control):
        if control == self.left.menu:
            select = control.getSelectedItem()
            self.update_center(select.getLabel())

        
    def update_center(self, n = "default"):
        print "%s : %s" % (n, DB.get_room_by_name(n))
        if n != "default":
            dev = DB.search_devices(room_id = DB.get_room_by_name(n).id)
            devices = []
            for d in dev:
                this_dev = ()

            print devices 
        else:
            devices = [("type1","techno1", 1, "%s1" % n, "value1"),
            ("type2","techno2", 2, "%s2" % n, "value2"),
            ("type3","techno3", 3, "%s3" % n, "value3"),
            ("type4","techno4", 4, "%s4" % n, "value4"),
            ("type5","techno5", 5, "%s5" % n, "value5"),
            ("type6","techno6", 6, "%s6" % n, "value6"),
            ("type7","techno7", 7, "%s7" % n, "value7"),
            ("type8","techno8", 8, "%s8" % n, "value8"),
            ("type9","techno9", 9, "%s9" % n, "value9"),
            ("type10","techno10", 10, "%s10" % n, "value10"),
            ("type11","techno11", 11, "%s11" % n, "value11"),
            ("type12","techno12", 12, "%s12" % n, "value12"),
            ("type13","techno13", 13, "%s13" % n, "value13"),]
        if self._set is not None:
            del self._set
        xbmcgui.lock()
        self._set = DeviceSet(self, self.left.menu, 150, 100, 4, devices)
        xbmcgui.unlock()
        #self.setFocus(self.left.menu)
    
w = DMGWindow()
w.doModal()

del w
