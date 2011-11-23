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

This file is part of 'ar_tank' hardware plugin

Get water level of your tank

This arduino program may be used without Domogik with any xPL project

@author: Fritz <fritz.smh@gmail.com>
@copyright: (C) 2007-2011 Domogik project
@license: GPL(v3)
@organization: Domogik

HC-SR04 datasheet : http://avrproject.ru/sonar_hc_sr04/HC-SR04.pdf
*/

/***********************************************
   sendHbeat
   Send a xPL hbeat message on serial 
   Input : n/a
   Output : n/a
***********************************************/

void sendHbeat() {
    char buffer[200];

    /**** header ****/
    sprintf(buffer, "xpl-stat\n{\n");
    sprintf(buffer, "%shop=1\n", buffer);
    sprintf(buffer, "%ssource=%s\n", buffer, MY_SOURCE);
    sprintf(buffer, "%starget=*\n}\n", buffer);

    /**** body : specification part ****/
    sprintf(buffer, "%shbeat.basic\n{\n", buffer);
    sprintf(buffer, "%sinterval=%i\n", buffer, HBEAT_INTERVAL);

    sprintf(buffer, "%s}\n", buffer);
    
    /**** Send it ****/
    Serial.println(buffer);   
}


/***********************************************
   sendSensorBasic
   Send a xPL sensor.basic message on serial 
   Input : string : type
           string : device 
           string : current
           string : units
   Output : n/a
***********************************************/

void sendSensorBasic(char *type, char *device, char *current, char *units) {
    char buffer[200];

    /**** header ****/
    sprintf(buffer, "xpl-stat\n{\n");
    sprintf(buffer, "%shop=1\n", buffer);
    sprintf(buffer, "%ssource=%s\n", buffer, MY_SOURCE);
    sprintf(buffer, "%starget=*\n}\n", buffer);

    /**** body ****/
    sprintf(buffer, "%ssensor.basic\n{\n", buffer);
    sprintf(buffer, "%stype=%s\n", buffer, type);
    sprintf(buffer, "%sdevice=%s\n", buffer, device);
    sprintf(buffer, "%scurrent=%s\n", buffer, current);
    sprintf(buffer, "%sunits=%s\n", buffer, units);

    sprintf(buffer, "%s}\n", buffer);
    
    /**** Send it ****/
    Serial.println(buffer);   
}

