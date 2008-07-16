#!/usr/bin/python
#-*- encoding:utf-8 *-*

# Author: Maxence Dunnewind <maxence@dunnewind.net>
#
# This is the MPD support for MPRIS
# See mpris.py and http://wiki.xmms2.xmms.se/wiki/Media_Player_Interfaces

# Core dbus stuff
import dbus

# Core MPD stuff
import mpd

class mprisMPD(dbus.service.Object):


            
    
    def __init__(self, object_path):
        __mpd = mpd.MPDClient()
        dbus.service.Object.__init__(self, dbus.SessionBus(), path)
        @dbus.service.method(dbus_interface='org.freedesktop.MediaPlayer')
        @dbus.service.signal(dbus_interface='org.freedesktop.MediaPlayer')

    def Identity(self):
        """
        Returns a string containing the media player identification
        """
        pass #self._mpd. 

    def Quit(self):
        """
        Makes the "Media Player" exit
        """
        pass

    def MprisVersion(self):
        """
        Returns a struct that represents the version of the MPRIS spec being implemented, organized as follows:
            uint16 major version (Existing API change)
            uint16 minor version (API addition) 
        """
        pass
    
    def GetMetadata(self, position):
        """
        Gives all meta data available for element at given position in the TrackList, counting from 0. 
        """
        pass

    def GetCurrentTrack(self):
        """
        Return the position of current URI in the TrackList
        The return value is zero-based, so the position of the first URI in the TrackList is 0.
        The behavior of this method is unspecified if there are zero elements in the TrackList.
        """
        pass
    
    def GetLength(self):
        """
        Number of elements in the TrackList
        """
        pass
        
    def AddTrack(self):
        """
        Appends an URI in the TrackList 
        """
        pass
        
    def DelTrack(self, track_position):
        """
        Removes an URI from the TrackList.
        """
        pass
        
    def SetLoop(self, loop):
        """
        Toggle playlist loop
        """
        pass
        
    def SetRandom(self, random):
        """
        Toggle playlist shuffle / random. It may or may not play tracks only once. 
        """
        pass
    
    def Next(self):
        """
        Goes to the next element
        """
        pass
        
    def Prev(self):
        """
        Goes to the previous element
        """
        pass
        
    def Pause(self):
        """
        If playing : pause. If paused : unpause
        """
        pass
    
    def Stop(self):
        """
        Stop playing
        """
        pass
    
    def Play(self):
        """
        If playing : rewind to the beginning of current track, else : start playing
        """
        pass
    
    def Repeat(self, repeat):
        """
        Toggle the current track repeat
        """
        pass
        
    def GetStatus(self):
        """
        Return the status of "Media Player" as a struct of 4 ints:
            First integer: 0 = Playing, 1 = Paused, 2 = Stopped.
            Second interger: 0 = Playing linearly , 1 = Playing randomly.
            Third integer: 0 = Go to the next element once the current has finished playing , 1 = Repeat the current element
            Fourth integer: 0 = Stop playing once the last element has been played, 1 = Never give up playing
        """
        pass
        
    def GetMetadata(self):
        """
        Gives all meta data available for the currently played element 
        """
        pass
        
    def GetCaps(self):
        """
        Return the "media player"'s current capabilities
        """
        pass
    
    def VolumeSet(self, level):
        """
        Sets the volume (argument must be in [0;100]) 
        """
        pass
        
    def VolumeGet(self):
        """
        Returns the current volume (must be in [0;100])
        """
        pass
        
    def PositionSet(self, position):
        """
        Sets the playing position (argument must be in [0;<track_length>] in milliseconds) 
        """
        pass
    
    def PositionGet(self):
        """
        Returns the playing position (will be [0;<track_length>] in milliseconds) 
        """
        pass
        
    def TrackChange(self, items, values):
        """
        Signal is emitted when the "Media Player" plays another "Track". 
        Argument of the signal is the metadata attached to the new "Track"
        """
        pass
        
    def StatusChange(self, state, random, repeat, loop):
        """
        Signal is emitted when the status of the "Media Player" change. 
        The argument has the same meaning as the value returned by GetStatus.
        """ 
        pass
        
    def CapsChange(self, capabilities):
        """
        Signal is emitted when the "Media Player" changes capabilities, see GetCaps method.
        """
        pass
        
    def  TrackListChange(self, elementsCount):
        """
        Signal is emitted when the "TrackList" content has changed: 
            *  When one or more elements have been added
            * When one or more elements have been removed
            * When the ordering of elements has changed
        The argument is the number of elements in the TrackList after the change happened. 
        """
        pass