


/***********************************************
   ftoa
   Convert a float value in string for direct usage in sprintf
   Input : buffer string, float value, precision to display
   Output : value converted in string
   Source : http://www.arduino.cc/cgi-bin/yabb2/YaBB.pl?num=1164927646/6#6
***********************************************/
char *ftoa(char *a, double f, int precision) {
    long p[] = {0,10,100,1000,10000,100000,1000000,10000000,100000000};
  
    char *ret = a;
    long heiltal = (long)f;
    itoa(heiltal, a, 10);
    while (*a != '\0') a++;
        *a++ = '.';
    long desimal = abs((long)((f - heiltal) * p[precision]));
    itoa(desimal, a, 10);
    return ret;
}
