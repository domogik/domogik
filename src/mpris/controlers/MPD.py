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

- MPD.__init__(self)
- MPD.Version(self)
- MPD.GetTrackInformation(self, position)
- MPD.GetCurrentTrackPosition(self)
- MPD.GetPlayListLength(self)
- MPD.AppendTrack(self, uri)
- MPD.PlayTrack(self, id)
- MPD.DeleteTrack(self, position)
- MPD.SetRepeat(self, enable)
- MPD.SetRandom(self, enable)
- MPD.Next(self)
- MPD.Prev(self)
- MPD.Pause(self)
- MPD.Stop(self)
- MPD.Play(self)
- MPD.GetPlayerProperties(self)
- MPD.GetCurrentTrackInformation(self)
- MPD.SetVolume(self, level)
- MPD.GetVolume(self)
- MPD.SetPosition(self, position)
- MPD.GetPosition(self)

@author: Maxence Dunnewind <maxence@dunnewind.net>
@copyright: (C) 2007-2012 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

import mpd
import GenericController

class MPD(GenericController):

    def __init__(self):
        self.__mpd = mpd.MPDClient()
        self.__mpd.connect("localhost", 6600)

    def Version(self):
        return self.__mpd.mpd_version

    def GetTrackInformation(self, position):
        return self.__mpd.playlistinfo()[position]

    def GetCurrentTrackPosition(self):
        return int(self.__mpd.currentsong()['pos'])

    def GetPlayListLength(self):
        return int(self.__mpd.status()['playlistlength'])

    def AppendTrack(self, uri):
        return self.__mpd.addid(uri)

    def PlayTrack(self, id):
        self.__mpd.playid(id)

    def DeleteTrack(self, position):
        self.__mpd.deleteid(position)

    def SetRepeat(self, enable):
        self.__mpd.repeat(int(enable))

    def SetRandom(self, enable):
        self.__mpd.random(int(enable))

    def Next(self):
        self.__mpd.next()

    def Prev(self):
        self.__mpd.previous()

    def Pause(self):
        self.__mpd.pause()

    def Stop(self):
        self.__mpd.stop()

    def Play(self):
        self.__mpd.play()

    def GetPlayerProperties(self):
        state = {
            'play': 0,
            'pause': 1,
            'stop': 2,
        }
        status = self.__mpd.status()
        return {
            'state': state[status['state']],
            'random': int(status['random']),
            'loop': 0,
            'repeat': int(status['repeat']),
        }

    def GetCurrentTrackInformation(self):
        return self.__mpd.currentsong()

    def SetVolume(self, level):
        self.__mpd.setvol(level)

    def GetVolume(self):
        return self.__mpd.status()['volume']

    def SetPosition(self, position):
        self.__mpd.seekid(int(self.__mpd.currentsong()['id']), position)

    def GetPosition(self):
        return int(self.__mpd.status()['time'].split(':')[0])
