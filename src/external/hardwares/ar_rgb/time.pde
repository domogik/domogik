/*
This file is part of B{Domogik} project (U{http://www.domogik.org}).

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

This file is part of 'ar_rgb' hardware plugin

Control RGB led strip with an arduino and xPL protocol

This arduino program may be used without Domogik with any xPL project

@author: Fritz <fritz.smh@gmail.com>
@copyright: (C) 2007-2011 Domogik project
@license: GPL(v3)
@organization: Domogik
*/

long previousSecond = 0;

/***********************************************
   pulse
   Set a var to 1 each second. 
   Input : n/a
   Output : n/a
   Note : you need to declare a "int second = 0" var in main pde file
***********************************************/

void pulse() {
    if (abs(millis() - previousSecond) > 1000) {
        second = 1;
        previousSecond = millis();
    }
    else {
        second = 0; 
    }
}

