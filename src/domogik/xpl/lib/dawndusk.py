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

Send events at dawn/duskl

Implements
==========

- DawnDusk:.__init__(self)
- DawnDusk:.get_dawn_dusk(self, long, lat, fh)

@author: Maxence Dunnewind <maxence@dunnewind.net>
@copyright: (C) 2007-2009 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

import datetime
import math


class DawnDusk:

    def __init__(self):
        pass

    def get_dawn_dusk(self, lgt, lat, fh):
        k = .0172024
        jm = 308.67
        jl = 21.55
        e = .0167
        ob = .4091
        pi = 3.141593
        dr = pi / 180
        hr = pi / 12
        # Sunrise and sunset sun height
        ht = (-50 / 60) * dr
        # Longitude and Latitude
        lo = lgt * dr
        la = lat * dr
        # Getting the current day of month
        today = datetime.date.today()
        jo = today.day
        mo = today.month
        if mo < 3:
            mo = mo + 12
        h = 12 + lo / hr
        # Number of days since 0,march,1
        j = int(30.61 * (mo + 1)) + jo + h / 24 - 123
        # Anomaly and average longitude
        m = k * (j - jm)
        l = k * (j - jl)
        # Real Longitude
        s = l + 2 * e * math.sin(m) + 1.25 * e * e * math.sin(2 * m)
        # Cartesian coordinates
        x = math.cos(s)
        y = math.cos(ob) * math.sin(s)
        z = math.sin(ob) * math.sin(s)
        # Time's equation and variation
        r = l
        rx = math.cos(r) * x + math.sin(r) * y
        ry = -1 * math.sin(r) * x + math.cos(r) * y
        x = rx
        y = ry
        et = math.atan(y / x)
        dc = math.atan(z / math.sqrt(1 - z * z))
        # Hour crossing the Meridien
        pm = h + fh + et / hr
        hs = int(pm)
        pm = 60 * (pm - hs)
        ms = int(pm)
        pm = 60 * (pm - ms)
        midi = (hs, ms, pm)
        # Sunrise and sunset clockwise sun angle
        cs = (math.sin(ht) - math.sin(la) * math.sin(dc)) \
                / math.cos(la) / math.cos(dc)
        if cs > 1 or cs < -1:
            ah = None
        else:
            if cs == 0:
                ah = pi / 2
            else:
                ah = math.atan(math.sqrt(1 - cs * cs) / cs)
            if cs < 0:
                ah = ah + pi
        # Sunrise
        pm = h + fh + (et - ah) / hr
        if pm < 0:
            pm = pm + 24
        hs = int(pm)
        pm = 60 * (pm - hs)
        lever = (hs, pm)
        # Sunset
        pm = h + fh + (et + ah) / hr
        if pm > 24:
            pm = pm - 24
        hs = int(pm)
        pm = 60 * (pm - hs)
        coucher = (hs, pm)
        return lever, coucher

if __name__ == "__main__":
    dd = DawnDusk()
    l, c = dd.get_dawn_dusk(-01.7075, 48.1173, 1)
    print(l)
    print(c)
