/*

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
    if ((millis() - previousSecond) > 1000) {
        second = 1;
        previousSecond = millis();
    }
    else {
        second = 0; 
    }
}

