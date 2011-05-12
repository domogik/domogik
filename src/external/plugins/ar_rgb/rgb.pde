
/*


*/

/***********************************************
   setColorFromRGBCode
   transform a #rrggbb to red, green and blue values and call setColorFromRGB
   Input : color in #rrggbb format (char)
   Output : n/a
***********************************************/
void setColorFromRGBCode(char color[8]) {
    Serial.println("call setColorFromRGBCode");
    Serial.print("Set color to : ");
    Serial.println(color);
    int red;
    int green;
    int blue;
    // we translate each value in decimal
    // remember that format is #rrggbb with rrggbb hexadecimal data
    red = getDecimal(color[1]) * 16 + getDecimal(color[2]);
    green = getDecimal(color[3]) * 16 + getDecimal(color[4]);
    blue = getDecimal(color[5]) * 16 + getDecimal(color[6]);
    Serial.println(red);
    Serial.println(green);
    Serial.println(blue);
    setColorFromRGB(red, green, blue);
}




/***********************************************
   setColorOff
   Set color to #000000
   Input : n/a
   Output : n/a
***********************************************/
void setColorOff() {
    Serial.println("call setColorOff");
    Serial.println("Off");
    setColorFromRGB(0, 0, 0);
}





/***********************************************
   setColorOn
   Set color to saved color
   Input : n/a
   Output : n/a
***********************************************/
void setColorOn() {
    Serial.println("call setColorOn");
    Serial.println("On");
    if ((currentColor[0] == 0) && (currentColor[1] == 0) && (currentColor[2] == 0)) {
        Serial.println("Set default color for on : #ffffff");
        setColorFromRGB(255, 255, 255);
    }
    else {
        setColorFromRGB(currentColor[0], currentColor[1], currentColor[2]);
    }
    // TODO : get last value and set it. If #000000 set #ffffff
    Serial.println("end of on");
}







/***********************************************
   setColorFromRGB
   Set color to PWM outputs
   Input : red (int), green (int), blue (int), color in #rrggbb format (char)
   Output : n/a
***********************************************/
void setColorFromRGB(int redValue, int greenValue, int blueValue) {
    Serial.println("call setColorFromRGB");
    char color[8];
    // Create color code from values
    sprintf(color, "#%02x%02x%02x", redValue, greenValue, blueValue);
  
    // set led color 
    // red, green, blue : 0..255  
    analogWrite(RED_PIN, redValue);
    analogWrite(GREEN_PIN, greenValue);
    analogWrite(BLUE_PIN, blueValue);
    // Save color only if different from #000000
    if (!((redValue == 0) && (greenValue == 0 ) && (blueValue == 0))) {
        currentColor[0] = redValue;
        currentColor[1] = greenValue;
        currentColor[2] = blueValue;
    }
    Serial.println(redValue);
    Serial.println(greenValue);
    Serial.println(blueValue);
    Serial.print("i have set color : ");
    Serial.println(color);
    sendXplTrigForSetColor(color);
    delay(100);
    return;   
}








/***********************************************
   getDecimal
   Get decimal value from a hexadecimal char
   Input : hex value (char) 
   Output : decimal (int)
***********************************************/
int getDecimal(char value) {
    int decimal = 0;
    if ((value >= 'a') && (value <= 'f')) {
        decimal = value - 'a' + 10;
    }
    if ((value >= 'A') && (value <= 'F')) {
        decimal = value - 'A' + 10;
    }
    if ((value >= '0') && (value <= '9')) {
        decimal = value - '0';
    }
    return decimal;
}




/***********************************************
   setColorFromHSL
   set color from Hue, Saturation and Luminosity
   Input : hue, saturation, luminosity (0...1)
   Output : n/a
***********************************************/
void setColorFromHSL(float H, float S, float L) {
    // HSL : 0..1
    // RGB : 0..255
    float R;
    float G;
    float B;
    float var1;
    float var2;
    
    Serial.print("H=");
    Serial.println(H);
    Serial.print("S=");
    Serial.println(S);
    Serial.print("L=");
    Serial.println(L);


    if (S == 0.0) {
        R = L*255.0;
        G = L*255.0;
        B = L*255.0;
    }
    else { 
        if (L < 0.5) {
            var2 = L*(1.0+S);
        }
        else {
            var2 = (L+S)-(S*L);
        }
        var1 = 2.0*L-var2;

        R = 255*hue2RGB(var1, var2, H+(1.0/3.0));
        G = 255*hue2RGB(var1, var2, H);
        B = 255*hue2RGB(var1, var2, H-(1.0/3.0));
    }
    Serial.print("R=");
    Serial.println(R);
    Serial.print("G=");
    Serial.println(G);
    Serial.print("B=");
    Serial.println(B);
    setColorFromRGB((int) R, (int) G, (int) B);
    return;
}



/***********************************************
   hue2RGB
   Help for setColorFromHSL function
   Input : var1, var2, hue
   Output : red, green or blue value
***********************************************/
float hue2RGB(float v1, float v2, float vH) {
   if (vH < 0.0) vH += 1.0;
   if (vH > 1.0) vH -= 1.0;
   if ((6.0*vH ) < 1.0) return (v1+(v2-v1)*6.0*vH);
   if ((2.0*vH ) < 1.0) return (v2);
   if ((3.0*vH ) < 2.0) return (v1+(v2-v1)*((2.0/3.0)-vH)*6.0);
   return v1;
}



