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

Module purpose
==============



Implements
==========

- Root:.__init__(self, session_bus, object_path, mainloop)
- Root:.GetIdentity(self)
- Root:.Quit(self)
- Root:.GetMprisVersion(self)
- TrackList:.GetMetaData(self, position)
- TrackList:.GetCurrentTrack(self)
- TrackList:.GetLength(self)
- TrackList:.AddTrack(self, uri, shouldBePlayedImmediately)
- TrackList:.DelTrack(self, position)
- TrackList:.SetLoop(self, isLoop)
- TrackList:.SetRandom(self, isRandom)
- Player:.Next(self)
- Player:.Prev(self)
- Player:.Pause(self)
- Player:.Stop(self)
- Player:.Play(self)
- Player:.Repeat(self)
- Player:.GetStatus(self)
- Player:.GetMetaData(self)
- Player:.GetCaps(self)
- Player:.VolumeSet(self, volume)
- Player:.VolumeGet(self)
- Player:.PositionSet(self, position)
- Player:.PositionGet(self)
- Player:.TrackChange(self, metaData):#userDefinedTrackChange(metaData))
- Player:.StatusChange(self)
- Player:.CapsChange(self)
- Player:.SetTrackChangeCb(self, cb)

@author: Domogik project
@copyright: (C) 2007-2009 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

import dbus
import dbus.glib

# Timer
import gobject

# File loading
import os

global client


class Root:

    def __init__(self, session_bus, object_path, mainloop):
        global client
        self.__mplayer = client
        self.__mainloop = mainloop
        dbus.service.Object.__init__(self, session_bus, object_path)

    # FIXME: should go into the docstring
    # Identify the "media player" as in "VLC 0.9.0", "bmpx 0.34.9",
    # "Audacious 1.4.0" ...

    def GetIdentity(self):
        return self.__root.Identity()

    # FIXME: should go into the docstring
    # Makes the "Media Player" exit

    def Quit(self):
        pass

    # FIXME: should go into the docstring
    # Get Mpris version

    def GetMprisVersion(self):
        pass


class TrackList:

    # FIXME: should go into the docstring
    # Gives all meta data available for element at given position in the
    # TrackList, counting from 0
    # Arguments
    # * Position in the TrackList of the item of which the metadata is
    # requested : int
    # Return value : the metadata : string

    def GetMetaData(self, position):
        pass

    # FIXME: should go into the docstring
    # Returns the position of current URI in the TrackList The return value
    # is zero-based, so the position of the first URI in the TrackList is 0.
    # The behavior of this method is unspecified if there are zero elements
    # in the TrackList.
    # Return value : position in the TrackList of the active element : int

    def GetCurrentTrack(self):
        pass

    # FIXME: should go into the docstring
    # Returns the number of elements in the TrackList
    # Return value : number of elements in the TrackList : int

    def GetLength(self):
        pass

    # FIXME: should go into the docstring
    # Appends an URI in the TrackList
    # Arguments :
    # * The uri of the item to append : string
    # * TRUE if the item should be played immediately,FALSE otherwise: boolean
    # Return value : 0 means Success : int

    def AddTrack(self, uri, shouldBePlayedImmediately):
        return 0

    # FIXME: should go into the docstring
    # Removes an URI from the TrackList
    # Arguments :
    # * Position in the tracklist of the item to remove : int

    def DelTrack(self, position):
        pass

    # FIXME: should go into the docstring
    # Toggle playlist loop
    # Arguments :
    # * TRUE to loop, FALSE to stop looping : boolean

    def SetLoop(self, isLoop):
        pass

    # FIXME: should go into the docstring
    # Toggle playlist shuffle / random. It may or may not play tracks only
    # once
    # Arguments :
    # * TRUE to play randomly / shuffle playlist, FALSE to play normally /
    # reorder playlist : boolean

    def SetRandom(self, isRandom):
        pass


class Player:

    def Next(self):
        # Goes to the next element
        pass

    def Prev(self):
        # Goes to the previous element
        pass

    def Pause(self):
        # Pause
        pass

    def Stop(self):
        # Stop
        pass

    def Play(self):
        # Play
        pass

    def Repeat(self):
        # Toggle the current track repeat
        # Arguments:
        # * TRUE to repeat the current track, FALSE to stop repeating : boolean
        pass

    def GetStatus(self):
        # Returns the status of "Media Player" as a struct of 4 ints:
        # * First integer: 0 = Playing, 1 = Paused, 2 = Stopped.
        # * Second interger: 0 = Playing linearly , 1 = Playing randomly.
        # * Third integer: 0 = Go to the next element once the current has
        #       finished playing , 1 = Repeat the current element
        # * Fourth integer: 0 = Stop playing once the last element has been
        #       played, 1 = Never give up playing
        return self.__status

    def GetMetaData(self):
        # Gives all meta data available for the currently played element
        pass

    def GetCaps(self):
        # Returns the "media player"'s current capabilities
        # NONE                  = 0,
        # CAN_GO_NEXT           = 1 << 0,
        # CAN_GO_PREV           = 1 << 1,
        # CAN_PAUSE             = 1 << 2,
        # CAN_PLAY              = 1 << 3,
        # CAN_SEEK              = 1 << 4,
        # CAN_PROVIDE_METADATA  = 1 << 5,
        # CAN_HAS_TRACKLIST     = 1 << 6
        pass

    def VolumeSet(self, volume):
        # Sets the volume (argument must be in [0;100])
        self.__volume = volume

    def VolumeGet(self):
        # Returns the current volume (must be in [0;100])
        return self.__volume

    def PositionSet(self, position):
        # Sets the playing position (argument must be in [0;<track_length>]
        # in milliseconds)
        self.__position = position

    def PositionGet(self):
        # Returns the playing position (will be [0;<track_length>]
        # in milliseconds)
        return self.__position

    ### Signals

    def TrackChange(self, metaData):#userDefinedTrackChange(metaData)):
        # Signal is emitted when the "Media Player" plays another "Track"
        # Arguments :
        # * a user defined function with argument that is the metadata
        # attached to the new "Track"
        self.__userDefinedTrackChange(metaData)

    def StatusChange(self):
        # Signal is emitted when the status of the "Media Player" change.
        # The argument  has the same meaning as the value returned by GetStatus
        pass

    def CapsChange(self):
        # Signal is emitted when the "Media Player" changes capabilities,
        # see getCaps method
        pass

    ### User setters

    def SetTrackChangeCb(self, cb):
        self.__userDefinedTrackChange = cb

if __name__ == "__main__":
    session_bus = dbus.SessionBus()
    dbus_names = session_bus.get_object("org.freedesktop.DBus",
        "/org/freedesktop/DBus")

    dbus_o = session_bus.get_object("org.freedesktop.DBus", "/")
    dbus_intf = dbus.Interface(dbus_o, "org.freedesktop.DBus")
    name_list = dbus_intf.ListNames()

    # Connect to the first Media Player found
    for name in name_list:
        print name
        if "org.mpris." in name:
            print "Found : ", name
            playerName = name
            break

    # first we connect to the objects
    root_o = bus.get_object(playerName, "/")
    player_o = bus.get_object(playerName, "/Player")
    tracklist_o = bus.get_object(playerName, "/TrackList")

    # there is only 1 interface per object
    root = dbus.Interface(root_o, "org.freedesktop.MediaPlayer")
    tracklist = dbus.Interface(tracklist_o, "org.freedesktop.MediaPlayer")
    player = dbus.Interface(player_o, "org.freedesktop.MediaPlayer")

    # self.__root = dbus.Interface(root_o, "org.freedesktop.MediaPlayer")
    # self.__tracklist  = dbus.Interface(tracklist_o,
    #         "org.freedesktop.MediaPlayer")
    # self.__player = dbus.Interface(player_o, "org.freedesktop.MediaPlayer")
