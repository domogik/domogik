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

// caracter codes 
#define END_OF_LINE     10       // \n
#define OPEN_BRACKET    "{"
#define CLOSE_BRACKET   "}"



/***********************************************
   sendHbeat
   Send a xPL hbeat message
   Input : n/a
   Output : n/a
***********************************************/
void sendHbeat() {
    Serial.println("Send hbeat message");
    char buffer[200];

    /**** header ****/
    sprintf(buffer, "xpl-stat\n{\n");
    sprintf(buffer, "%shop=1\n", buffer);
    sprintf(buffer, "%ssource=%s\n", buffer, MY_SOURCE);
    sprintf(buffer, "%starget=*\n}\n", buffer);

    /**** body : specification part ****/
    sprintf(buffer, "%shbeat.basic\n{\n", buffer);
    sprintf(buffer, "%sinterval=%i\n", buffer, HBEAT_INTERVAL);
    sprintf(buffer, "%sport=%u\n", buffer, localPort);

    /**** body : developper part ***/
    // ip
    sprintf(buffer, "%sip=%i.%i.%i.%i\n", buffer, ip[0], ip[1], ip[2], ip[3]);
    // mac address
    sprintf(buffer, "%smac=%x:%x:%x:%x:%x:%x\n", buffer, mac[0], mac[1], mac[2], mac[3], mac[4], mac[5]);
    // current color
    sprintf(buffer, "%scolor=#%02x%02x%02x\n", buffer, currentColor[0], currentColor[1], currentColor[2]);

    sprintf(buffer, "%s}\n", buffer);
    
    //Serial.println(buffer);  

    /**** Send it ****/
    Udp.sendPacket(buffer, broadCastIp, xplPort);   
}


/***********************************************
   sendXplTrigForSetColor
   Send a xPL Trig message after setting a color
   Input : color code (#rrggbb format)
   Output : n/a
   
***********************************************/
void sendXplTrigForSetColor(char color[8]) {
    Serial.print("Send xpl-trig for setColor : ");
    Serial.println(color);
    char buffer[150];

    /**** header ****/
    sprintf(buffer, "xpl-trig\n{\n");
    sprintf(buffer, "%shop=1\n", buffer);
    sprintf(buffer, "%ssource=%s\n", buffer, MY_SOURCE);
    sprintf(buffer, "%starget=*\n}\n", buffer);

    /**** body ****/
    sprintf(buffer, "%sarduino.rgb\n{\n", buffer);
    sprintf(buffer, "%scommand=setcolor\n", buffer);
    sprintf(buffer, "%sdevice=%s\n", buffer, MY_DEVICE);
    sprintf(buffer, "%scolor=%s\n", buffer, color);

    sprintf(buffer, "%s}\n", buffer);

    /**** Send it ****/
    //Serial.println(buffer);
    Udp.sendPacket(buffer, broadCastIp, xplPort);   
}


/***********************************************
   parseXpl
   parse a xpl message
   Input : message (byte)
           message size (int)
   Output : code (int) : 0 = success
                         not 0 = not a valid message
***********************************************/
int parseXpl(byte *received, int len)
{
    Serial.println("Start parsing message");

    /* specification values */
    //char buffer[144+1+1]; //16+'='+128 : format : "key=value"
    //char key[16+1];
    //char value[128+1]; 
    
    /* optimised values for arduino.rgb message */
    char buffer[36+1+1]; //16+'='+20 : format : "key=value"
    char key[16+1];
    char value[20+1]; 

    /**** specific to arduino.rgb message processing ****/
    char myType[8+1];       // xpl-stat, xpl-cmnd, xpl-trig
    char mySchema[8+1+8+1]; // <class>.<type>
    char myDevice[16+1];    // in practice, this could be sized up to 128, but here device should be the same as the instance (max : 16)
    char myCommand[16+1];   // setcolor, etc... could be sized up to 128, but we use short commands here
    char myColor[7+1];      // format : #rrggbb
    // Init color to 'None' value
    //sprintf(myColor, "%s", "None");
    
    int j=0;
    int line=0;
    int result=0;
    
    int xpl_part = 0;  // 0 : message type
                       // 1 : header
                       // 2 : schema
                       // 3 : body
                       
    // Message processing
    // Read each character of the message
    for(int i=0; i<len; i++){
        // load byte by byte in 'line' buffer, until '\n' is detected

        if(received[i]== END_OF_LINE) { // is it a linefeed (ASCII: 10 decimal)
            buffer[j]='\0';    // add the end of string id
            //Serial.print("line=");
            //Serial.println(buffer);
            line++;
             
            if (strcmp(buffer, OPEN_BRACKET) == 0) {
                Serial.println ("Open bracket");
                xpl_part++; 
            } 
            else if (strcmp(buffer, CLOSE_BRACKET) == 0) {
                Serial.println("Close bracket");                
                xpl_part++; 
            }
            else {
            // xpl type (first line)
                if (xpl_part == 0) {
                    Serial.print("Message type : ");
                    Serial.println(buffer);
                    sprintf(myType, "%s", buffer);
                
                    // eventually add a filter here on xpl type
                    if (strcmp(buffer, "xpl-cmnd")  != 0) {
                        //Serial.println("Filtered!");
                        return 1;
                    }
                
                }   
                // header      
                else if (xpl_part == 1) {
                    //If necessary, add code here to check header
                    Serial.println("Header");
                }
                // schema
                else if (xpl_part == 2) {
                    Serial.print("schema : ");
                    Serial.println(buffer);
                    sprintf(mySchema, "%s", buffer);
                       
                    // eventually add a filter here on schema
                    // warning : if you test on "foo.basic", "foo.basicx" will be accepted unless you add a dedicated test on length
                    if (strcmp(buffer, "arduino.rgb")  != 0) {
                        //Serial.println("Filtered!");
                        return 2;                
                    }
                }
                // body
                else if (xpl_part == 3) {
                    sscanf(buffer, "%[^'=']=%s", key, value);
                    Serial.print("Key : value =");
                    Serial.print(key);
                    Serial.print(" : ");
                    Serial.println(value);
                        
                    // Here, store data in appropriate vars for final processing
                    if (strcmp(key, "device")  == 0) {
                        sprintf(myDevice, "%s", value);
                    }
                    if (strcmp(key, "command")  == 0) {
                        sprintf(myCommand, "%s", value);
                    }
                    if (strcmp(key, "color")  == 0) {
                        sprintf(myColor, "%s", value);
                    }
                }
            }        
            
            j=0; // reset the buffer pointer
        }
        else {
            // put next character in buffer
            buffer[j]=received[i];
            j=j++;
        }
    }
    // End of message
    if (xpl_part >= 3) {
        Serial.println("Parsing finished");

        // Add here processing about xpl message

        /**** First, check type, schema and device targetted ****/
        // If no filters applied before (if your program may listen for several type/schema),
        // for each possible action, do a test like this : 
        /*
        if ((strcmp(myType, "xpl-cmnd") == 0) &&
            (strcmp(mySchema, "arduino.rgb") == 0) &&
            (strcmp(myDevice, MY_DEVICE) == 0)) { 
        */
        // Here, we already filtered on type and schema (and there was only one possibility available)
        // so, we check only targetted device
        if (strcmp(myDevice, MY_DEVICE) == 0) {
        
            /**** Set color ****/
            if (strcmp(myCommand, "setcolor")  == 0) {
                /**** Set on ****/
                if (strcmp(myColor, "on")  == 0) {
                    setColorOn();
                    Serial.println("After calling for on");
                }
                /**** Set off ****/
                else if (strcmp(myColor, "off")  == 0) {
                    setColorOff();
                }
                /**** Set color to color ****/
                else {
                    setColorFromRGBCode(myColor);
                }
            }     
        }
        return 0;
    }
    // If message has not the good format
    else {
        return 3;
    }   
}



