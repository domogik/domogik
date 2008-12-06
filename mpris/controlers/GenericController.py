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

# Author: Maxence Dunnewind <maxence@dunnewind.net>

# $LastChangedBy: mschneider $
# $LastChangedDate: 2008-12-06 16:30:18 +0100 (sam. 06 déc. 2008) $
# $LastChangedRevision: 234 $

#Interface for mpris support
#All controllers should extends this class

class NotImplementedException:
    """
        This class defines an exception which should be raised if a function hasn't be implemented
    """
    def __init__(self, value = "This method isn't implemented yet"):
        self.value = value
    
    def __str__(self):
        return self.repr(self.value)

class GenericController:

    def __init__(self):
        raise NotImplementedException

    def Version(self):
        """
            Returns player version
        """
        raise NotImplementedException

    def GetTrackInformation(self, position):
        """
            Gives all meta data available for element at given position (counting from 0)
        """
        raise NotImplementedException

    def GetCurrentTrackPosition(self):
        """
            Returns current song position (couting from 0)
        """
        raise NotImplementedException

    def GetPlayListLength(self):
        """
            Returns current playlist length
        """
        raise NotImplementedException

    def AppendTrack(self, uri, play):
        """
            Appends an URI to the current playlist
            Plays now if 'play' is True
        """
        raise NotImplementedException
    
    def DeleteTrack(self, position):
        """
            Removes an URI from current playlist
        """
        raise NotImplementedException

    def SetRepeat(self, enable):
        """
            Enables or disables repeat
        """
        raise NotImplementedException

    def SetRandom(self, enable):
        """
            Enables or disables random
        """
        raise NotImplementedException

    def Next(self):
        """
            Goes to the next element
        """
        raise NotImplementedException

    def Prev(self):
        """
            Goes to the previous element
        """
        raise NotImplementedException

    def Pause(self):
        """
            If playing : pause; if paused : unpause
        """
        raise NotImplementedException

    def Stop(self):
        """
            Stop playing
        """
        raise NotImplementedException

    def Play(self):
        """
            If playing : rewind to the beginning of current track, else : start playing
        """
        raise NotImplementedException

    def GetPlayerProperties(self):
        """
            Returns a dict of 4 string/ints
            'state' : 0 = Playing, 1 = Paused, 2 = Stopped.
            'random' : 0 = Playing linearly , 1 = Playing randomly.
            'loop' : 0 = Go to the next element once the current has finished playing , 1 = Repeat the current element
            'repeat' : 0 = Stop playing once the last element has been played, 1 = Never give up playing
        """
        raise NotImplementedException

    def GetCurrentTrackInformation(self):
        """
            Gives all meta data available for current element
        """
        raise NotImplementedException
        
    def SetVolume(self, level):
        """
            Set the volume (argument must be in [0;100]
        """
        raise NotImplementedException

    def GetVolume(self):
        """
            Returns the current volume
        """
        raise NotImplementedException

    def SetPosition(self, position):
        """
            Sets the playing position (argument must be in [0;<track length>]), in milliseconds
        """
        raise NotImplementedException

    def GetPosition(self):
        """
            Returns the playing position in milliseconds
        """
        raise NotImplementedException

