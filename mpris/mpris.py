#!/usr/bin/python
#-*- encoding:utf-8 *-*

# Copyright 2008 Domogik project

# This file is part of Domogik.
# Domogik is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# Domogik is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with Domogik.  If not, see <http://www.gnu.org/licenses/>.

# Author : Marc Schneider <marc@mirelsol.org>

# $LastChangedBy: mschneider $
# $LastChangedDate: 2008-07-23 21:42:29 +0200 (mer. 23 juil. 2008) $
# $LastChangedRevision: 100 $

# This is the mpris API
# See http://wiki.xmms2.xmms.se/wiki/Media_Player_Interfaces

# Core dbus stuff
import dbus
import dbus.glib

# Timer
import gobject

# File loading
import os

class Mpris:
    "mpris API"
    
    def __init__(self):
        # See getStatus method for more information
        self.__status = [0, 0, 0, 0]
        self.__volume = 0
        self.__position = 0
        self.__bus = dbus.SessionBus()
    
    def connect(self):
	    # First we connect to the objects
	    root_o = self.__bus.get_object(name, "/")
	    player_o = self.__bus.get_object(name, "/Player")
	    tracklist_o = self.__bus.get_object(name, "/TrackList")
	
 	    self.__root = dbus.Interface(root_o, "org.freedesktop.MediaPlayer")
	    self.__tracklist  = dbus.Interface(tracklist_o, "org.freedesktop.MediaPlayer")
	    self.__player = dbus.Interface(player_o, "org.freedesktop.MediaPlayer")
    
    ### ROOT methods
    
    # Identify the "media player" as in "VLC 0.9.0", "bmpx 0.34.9", "Audacious 1.4.0" ... 
    def getIdentity(self):
    	return self.__root.Identity()
    
    # Makes the "Media Player" exit
    def quit(self):
    	pass
    
    # Get Mpris version
    def getMprisVersion(self):
    	pass
    
    ### Tracklist methods
    
    # Gives all meta data available for element at given position in the TrackList, counting from 0
    # Arguments
    # * Position in the TrackList of the item of which the metadata is requested : int
    # Return value : the metadata : string
    def getTracklistMetaData(self, position):
    	pass
    
    # Returns the position of current URI in the TrackList The return value is zero-based, so the position of the first URI in the TrackList is 0. 
    # The behavior of this method is unspecified if there are zero elements in the TrackList.
    # Return value : position in the TrackList of the active element : int 
    def getCurrentTrack(self):
    	pass
    
    # Returns the number of elements in the TrackList
    # Return value : number of elements in the TrackList : int
    def getLength(self):
    	pass
    
    # Appends an URI in the TrackList
    # Arguments :
    # * The uri of the item to append : string
    # * TRUE if the item should be played immediately, FALSE otherwise : boolean 
    # Return value : 0 means Success : int
    def addTrack(self, uri, shouldBePlayedImmediately):
    	return 0
    
    # Removes an URI from the TrackList
    # Arguments :
    # * Position in the tracklist of the item to remove : int
    def delTrack(self, position):
    	pass
    
    # Toggle playlist loop
    # Arguments :
    # * TRUE to loop, FALSE to stop looping : boolean 
    def setLoop(self, isLoop):
    	pass
    
    # Toggle playlist shuffle / random. It may or may not play tracks only once
    # Arguments :
    # * TRUE to play randomly / shuffle playlist, FALSE to play normally / reorder playlist : boolean
    def setRandom(self, isRandom):
    	pass
    
    ### Player object methods
    
    # Goes to the next element
    def next(self):
    	pass
    
    # Goes to the previous element
    def prev(self):
    	pass
    
    # Pause
    def pause(self):
    	pass
    
    # Stop
    def stop(self):
    	pass
    
    # Play
    def play(self):
    	pass
    
    # Toggle the current track repeat
    # Arguments:
    # * TRUE to repeat the current track, FALSE to stop repeating : boolean
    def repeat(self):
    	pass
   
    # Returns the status of "Media Player" as a struct of 4 ints:
    # * First integer: 0 = Playing, 1 = Paused, 2 = Stopped.
    # * Second interger: 0 = Playing linearly , 1 = Playing randomly.
    # * Third integer: 0 = Go to the next element once the current has finished playing , 1 = Repeat the current element
    # * Fourth integer: 0 = Stop playing once the last element has been played, 1 = Never give up playing
    def getStatus(self):
    	return self.__status
    
    # Gives all meta data available for the currently played element
    def getElementMetaData(self):
    	pass
    
    # Returns the "media player"'s current capabilities
    def getCaps(self):
    	# NONE                  = 0,
        # CAN_GO_NEXT           = 1 << 0,
        # CAN_GO_PREV           = 1 << 1,
        # CAN_PAUSE             = 1 << 2,
        # CAN_PLAY              = 1 << 3,
        # CAN_SEEK              = 1 << 4,
        # CAN_PROVIDE_METADATA  = 1 << 5,
        # CAN_HAS_TRACKLIST     = 1 << 6
    	pass
    
    # Sets the volume (argument must be in [0;100])
    def volumeSet(self, volume):
    	self.__volume = volume
    
    # Returns the current volume (must be in [0;100])
    def volumeGet(self):
    	return self.__volume
    
    # Sets the playing position (argument must be in [0;<track_length>] in milliseconds)
    def positionSet(self, position):
    	self.__position = position
    
    # Returns the playing position (will be [0;<track_length>] in milliseconds)
    def positionGet(self):
    	return self.__position
    
    ### Signals
    
    # Signal is emitted when the "Media Player" plays another "Track"
    # Arguments :
    # * a user defined function with argument that is the metadata attached to the new "Track" 
    def trackChange(self, metaData):#userDefinedTrackChange(metaData)):
    	self.__userDefinedTrackChange(metaData)
    
    # Signal is emitted when the status of the "Media Player" change. The argument 
    # has the same meaning as the value returned by GetStatus
    def statusChange(self):
    	pass
    
    # Signal is emitted when the "Media Player" changes capabilities, see getCaps method
    def capsChange(self):
    	pass
    
    ### User setters
    def setTrackChangeCb(self, cb):
        self.__userDefinedTrackChange = cb
    



