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

#include <SPI.h>         // needed for Arduino versionslater than 0018
#include <Ethernet.h>
#include <Udp.h>


/***************** Network configuration ********************/

// Mac address : a mac address must be unique
byte mac[] = {0xDE, 0xAD, 0xBE, 0xEF, 0xFE, 0xED};
// IP address : the value will depend on your network
byte ip[] = {192, 168, 1, 160};
// Broadcat address's first three elements should be the same than ip. The last should be 255.
byte broadCastIp[] = {192, 168, 1, 255};
// Udp local port used (any value you want between 1024 and 65536)
unsigned int localPort = 3865;  
// xPL protocol port (keep default value unless you know what you are doing)
unsigned int xplPort = 3865;  

/***************** xPL configuration part *******************/

// Source. Format is <vendor id>-<device id>.<instance>

// Vendor id and device id should not be changed
// Instance should be the location of your arduino and RGB led strip : living, bedroom, etc
// Instance should only use letters or numbers! (no underscore, ...)
#define MY_SOURCE "arduino-rgb.parentsbedroom"

// Name of device in body of xpl message
// This should be the same as previously defined instance
#define MY_DEVICE "parentsbedroom"

// Maximal size of xPL messages that could be processed
// This size should not be reduce unless you are sure of what you are doing
#define MAX_XPL_MESSAGE_SIZE 165

// Heartbeat interval : time in minutes between 2 sends of a xpl hbeat message
#define HBEAT_INTERVAL 1

/******************** RGB configuration**********************/

// Define which PWM pins to use
#define RED_PIN 3
#define GREEN_PIN 5
#define BLUE_PIN 6

// define potentiometer pin
#define ANALOG_CONTROL A0

// define button pin
#define BUTTON_CONTROL 8

/******************* END OF CONFIGURATION *******************/


/********************* time management **********************/

int second = 0;
int lastHbeat = 0;

/*********************** Global vars ************************/

// current color
int isOff = true;
byte currentColor[] = {0x00, 0x00, 0x00};

// analog control value
int analogControlValue = 0;
int oldAnalogControlValue = 0;
float hue = 0;

// button control value
int buttonControlValue = 0;


// UDP related vars
UDP Udp;

int packetSize = 0;      // received packet's size
byte remoteIp[4];        // received packet's IP
unsigned int remotePort; // received packet's port
byte packetBuffer[MAX_XPL_MESSAGE_SIZE];   // place to store received packet

// status
int result;


/********************* Set up arduino ***********************/
void setup() {
    // Wait before doing anything
    delay(5000);
    
    // Serial debugging
    Serial.begin(115200);
    Serial.println("Setup arduino...");
    
    // Ethernet initialisation
    Ethernet.begin(mac, ip);
    Udp.begin(localPort);
    
    // Set pin's mode
    pinMode(RED_PIN, OUTPUT);
    pinMode(GREEN_PIN, OUTPUT);
    pinMode(BLUE_PIN, OUTPUT);
    pinMode(BUTTON_CONTROL, INPUT);
    
    // read analog control value
    analogControlValue = analogRead(ANALOG_CONTROL);
    oldAnalogControlValue = analogControlValue;
    
    // Send a hbeat message on startup
    sendHbeat();
    setColorOff();

    Serial.println("Setup arduino finished.");
}





/*********************** Processing *************************/
void loop() {
  
    /**** potentiometer management ****/
    
    analogControlValue = analogRead(ANALOG_CONTROL);
    if (abs(oldAnalogControlValue - analogControlValue) > 2) {
        Serial.print("Analog control : ");
        Serial.print(analogControlValue);
        Serial.print(" / ");
        Serial.println(analogControlValue);
        oldAnalogControlValue = analogControlValue;
        hue = analogControlValue / 1024.0;
        setColorFromHSL(hue, 1, 0.5);
    }
 
    /**** switch management ****/
    buttonControlValue = digitalRead(BUTTON_CONTROL);
    if (buttonControlValue == HIGH) {
        if (isOff == true) {
            setColorOn();
            Serial.println("button on");
        }
        else {
            setColorOff();
            Serial.println("button off");
        }
        // wait to avoid changes due to rebound on button
        delay(200);      
    }
 
    
    /**** pulse management ****/
    pulse();
    // Each second, make a pulse
    if (second == 1) {
        Serial.println("---- PULSE ----");
        
        // Hbeat
        lastHbeat += 1;
        
        // Each N minute, send a hbeat xpl message
        if (lastHbeat == (60*HBEAT_INTERVAL)) {
            sendHbeat();
            lastHbeat = 0;
        }
    }

    /**** Udp listening ****/
    packetSize = Udp.available(); // Size of detected packet
    // packet detection
    if (packetSize) { 
        Serial.print("UDP packet received of size : ");
        Serial.println(packetSize);

        // read the packet and get the senders IP address and the port number
        Udp.readPacket(packetBuffer,MAX_XPL_MESSAGE_SIZE, remoteIp, (uint16_t *)&remotePort);

        // if message is full (not truncated), process it :
        if(abs(packetSize) < MAX_XPL_MESSAGE_SIZE) {
            Serial.println("Message of good size");
            result = parseXpl(packetBuffer,abs(packetSize));
        }
        else {
            Serial.println("Message to big to be parsed");
        }
    }
}




