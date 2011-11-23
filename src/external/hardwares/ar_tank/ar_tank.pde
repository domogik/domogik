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

#define PIN_DISTANCE_TRIG 2      // on ECHO pin of HC-SR04
#define PIN_DISTANCE_ECHO 3      // on TRIG pin of HC-SR04

/***************** xPL configuration part *******************/

// Name of device in body of xpl message
#define MY_DEVICE "macuve"

// Source. Format is <vendor id>-<device id>.<instance>
// Vendor id and device id should not be changed
// Instance could be the device name 
// Instance should only use letters or numbers! (no underscore, ...)
#define MY_SOURCE "arduino-tank." MY_DEVICE

// Duration of a minute in seconds (to allow shorter delay in dev)
#define MINUTE 60

// Heartbeat interval : time in minutes between 2 sends of a xpl hbeat message
#define HBEAT_INTERVAL 5

// Values intervals : time in minutes between 2 sends of values
#define DISTANCE_INTERVAL 1

/******************** tank configuration ********************/

// tank total depth in centimeters
#define TANK_DEPTH 231
// distance between sensor and the max level of water in centimeters
#define TANK_ZERO 49

/********************* time management **********************/

int second = 0;
int lastTimeHbeat = 0;
int lastTimeDistance = 0;



void setup() {
    delay(10);    // in case of problem, it allows easier upload
    pinMode(PIN_DISTANCE_ECHO, OUTPUT);     
    pinMode(PIN_DISTANCE_TRIG, INPUT);   
    Serial.begin(9600);

    // Send a hbeat message on startup
    sendHbeat();
}


void loop() {    
    // pulse management 
    pulse();
    // Each second, check is it is time to make any action
    if (second == 1) {
        // Hbeat action
        lastTimeHbeat += 1;
        // Each N minute, send a hbeat xpl message
        if (lastTimeHbeat == (MINUTE*HBEAT_INTERVAL)) {
            sendHbeat();
            lastTimeHbeat = 0;
        }
        
        // Distance measurement
        lastTimeDistance += 1;
        // Each N minute, get distance
        if (lastTimeDistance == (MINUTE*DISTANCE_INTERVAL)) {
            // Get distance and send it
            float distance = getDistance();
            char strDistance[15];
            sendSensorBasic("distance", MY_DEVICE, ftoa(strDistance, distance, 2), "cm");
            int percent = distanceToPercent(distance);
            //strDistance[15];
            sendSensorBasic("percent", MY_DEVICE, ftoa(strDistance, percent, 2), "%");
            lastTimeDistance = 0;
        }        
    }
}


/***********************************************
   getDistance
   Get distance from a HC-SR04
   Input : n/a
   Output : distance in cm
***********************************************/
float getDistance() {
    // make sure to have a low level on ECHO pin
    digitalWrite(PIN_DISTANCE_ECHO, LOW);
    delayMicroseconds(2);   
    // send echo
    digitalWrite(PIN_DISTANCE_ECHO, HIGH);
    delayMicroseconds(10);   // 10us : indicated in datasheet
    digitalWrite(PIN_DISTANCE_ECHO, LOW);
    // get time response
    long responseTime = pulseIn(PIN_DISTANCE_TRIG, HIGH); // time for response in ms
    // convert time in distance (cm)
    // sound speed is 340m/s
    // here we have a time in microseconds and we want the distance in cm
    // equivalent sound speed is 34000cm/s
    //                           34cm/ms
    //                           0,034cm/us 
    // we will need to divide the result by 2 : the sound go to the object and come back
    float distance = 0.034 * responseTime / 2; 
    return distance;
}

/***********************************************
   distanceToPercent
   Get the % of tank filled
   Input : n/a
   Output : tank level in %
   Note : this function can return negativ values or values greater than 100%
           If this happens, the tank configuration is not good ;)
***********************************************/
float distanceToPercent(float distance) {
    int percent;
    int tankDepthFromZero = TANK_DEPTH - TANK_ZERO;
    float distanceFromZero = distance - TANK_ZERO;
    percent = 100 - (100 * distanceFromZero)/tankDepthFromZero;
    return percent;
}

