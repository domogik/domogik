/*

*/

#include <SPI.h>         // needed for Arduino versionslater than 0018
#include <Ethernet.h>
#include <Udp.h>



#include "memoryfree.h"













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
// !!!!!!!!!!!!!!!TODO : possible to use a define here for previous elements ?

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
#define MAX_XPL_MESSAGE_SIZE 150

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
#define BUTTON_CONTROL 1

/********************* time management **********************/

int second = 0;
int lastHbeat = 0;

/*********************** Global vars ************************/

// current color
byte currentColor[] = {0x00, 0x00, 0x00};

// analog control value
int analogControlValue = 0;
int oldAnalogControlValue = 0;
float hue = 0;

// button control value
int buttonControlValue = 0;
int oldButtonControlValue = 0;


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
    
    Serial.print("freeMemory()=");
    Serial.println(freeMemory());

    // Ethernet initialisation
    Ethernet.begin(mac, ip);
    Udp.begin(localPort);
    
    // Set pin's mode
    pinMode(RED_PIN, OUTPUT);
    pinMode(GREEN_PIN, OUTPUT);
    pinMode(BLUE_PIN, OUTPUT);

    pinMode(BUTTON_CONTROL, INPUT);
    buttonControlValue = 
    
    // read anallog control value
    analogControlValue = analogRead(ANALOG_CONTROL);
    oldAnalogControlValue = analogControlValue;
    
    // Send a hbeat message on startup
    sendHbeat();
    delay(100);
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
    if (buttonControlValue != oldButtonControlValue) {
        if (buttonControlValue == LOW) {
            setColorOn();
        }
        else {
            setColorOff();
        }
        oldButtonControlValue = buttonControlValue;
        delay(100);
      
    }
 
    
    /**** pulse management ****/
    pulse();
    if (second == 1) {
        Serial.println("!!! PULSE !!!");
        
        // Hbeat
        lastHbeat += 1;
        
        if (lastHbeat == (60*HBEAT_INTERVAL)) {
            Serial.println("----SH----");
            sendHbeat();
            
            delay(10);
            lastHbeat = 0;
        }
    }


    /**** Udp listening ****/
    packetSize = Udp.available(); // Size of detected packet
    if (packetSize) { // packet detected
        Serial.print("UDP packet received of size : ");
        Serial.println(packetSize);

        // read the packet and get the senders IP address and the port number
        Udp.readPacket(packetBuffer,MAX_XPL_MESSAGE_SIZE, remoteIp, (uint16_t *)&remotePort);

        // if message is full (not truncated), process it :
        if(abs(packetSize) < MAX_XPL_MESSAGE_SIZE) {
            Serial.println("Message of good size");
            result = parseXpl(packetBuffer,abs(packetSize));
            Serial.println("After parsing");
        }
        else {
            Serial.println("Message to big to be parsed");
        }
    }
}




