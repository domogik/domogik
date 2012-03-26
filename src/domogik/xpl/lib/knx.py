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

KNx Bus

Implements
==========

- KNX

@author: Fritz <fritz.smh@gmail.com> Basilic <Basilic3@hotmail.com>
@copyright: (C) 2007-2009 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

import subprocess


###decodage des valeurs en fonction du datapoint type
def decodeKNX(datatype, val):
   if datatype <> '' and val<>'':

  ### Decode the data function of the datapoint type
      if datatype == "1.001": #DT_switch
         val=int(val.replace(" ",""),16)
         if val==1:
            val="on"
         if val==0:
            val="off"

      if datatype=="1.008": #DT_UpDown
         val=int(val.replace(" ",""),16)
         if val<=1:        
            if val==1:
               val="Down"
            if val==0:
               val="Up"
 
      if datatype == "3.007": #DT_Control_Dimming
         val=int(val.replace(" ",""),16)
         if val>=1 and val <= 7:
            val= "dim-"
         if val>=9:
            val="dim+"
         if val==8 or val==0:
            val="stop"

      if datatype == "3.008": #DT_Control_Blinds
         val=int(val.replace(" ",""),16)
         if val>=1 and val <= 7:
            val= "up"
         if val>=9:
            val="down"
         if val==8 or val==0:
            val="stop"
 
      if datatype =="5.001": # "DT_Scaling"
         val=int(val.replace(" ",""),16)
         if val<=255:
            val=(100*int(val)/255)
 
      if datatype[:2] == "5." and  datatype!="5.001" and datatype!="5.003": #8bit unsigned integer
         val=int(val.replace(" ",""),16)
         if val<=255:
            val=val
 
      if datatype == "5.003": #DT_Angle
         val=int(val.replace(" ",""),16)
         if val<=255:
            val=val*360/255

      if datatype[:2] =="6.": #8bit signed integer (EIS14) 
         val=int(val.replace(" ",""),16)
         if val<128:
            val=val
         else:
            val=val-256

      if datatype[:2] =="7.": #16bit unsigned integer (EIS14) 
         val=int(val.replace(" ",""),16)
         if val<=65535:
            val=val

      if datatype[:2] =="8.": #16bit signed integer (EIS14) 
         val=int(val.replace(" ",""),16)
         if val<=65535:
            if val<=32767:
               val=val
            else:
               val=-65536+val

      if datatype[:2] =="9.": #16bit unsigned integer (EIS14) 
         val=int(val.replace(" ",""),16)
         if val<=65535:
            val=bin(val)[2:]
            if len(val)<=16:
               for i in range(16-len(val)):
                  val="0"+val
            Y=long(val[1:5],2)
            X=long(val[0:1]+val[5:16],2)
            if X>=2047:
               X=X-4096
            val=float(0.01*X*2**Y)

      if datatype =="10.001": #time (EIS3)
         val=int(val.replace(" ",""),16)
         if val!=0: #val<=347628       
            val=bin(val)[2:]
            second=int(val[len(val)-6:len(val)],2)
            val=val[0:len(val)-8]
            minute=int(val[len(val)-6:len(val)],2)
            val=val[0:len(val)-8]
            hour=int(val[len(val)-5:len(val)],2)
            val=val[0:len(val)-5]
            if len(val)>=1:
               day=int(val,2)
            else:
               day="No day"
            if len(str(hour))<2:
               hour="0"+str(hour)
            if len(str(minute))<2:
               minute="0"+minute
            if len(str(second))<2:
               second="0"+second
               val=str(hour)+":"+str(minute)+":"+str(second)+".0"

      if datatype =="11.001": #date (EIS4)
         val=int(val.replace(" ",""),16)
         if val!=0:
            val=bin(val)[2:]
            if len(val)<24:
               for i in range(24-len(val)):
                  val="0"+val
            year=int(val[len(val)-7:len(val)],2)
            val=val[0:len(val)-8]
            mounth=int(val[len(val)-4:len(val)],2)
            val=val[0:len(val)-8]
            day=int(val[len(val)-5:len(val)],2)
            if len(str(year))<2:
               year="0"+str(year)
            if len(str(mounth))<2:
               mounth="0"+str(mounth)
            if len(str(day))<2:
               day="0"+str(day)
            val=str(year)+"-"+str(mounth)+"-"+str(day)
     
      if datatype[:3] == "12.": #32 bit unsigned interger
         val=int(val.replace(" ",""),16)
         if val>=4294967296:
            val=val

      if datatype[:3] == "13.": #32bit signed integer
         val=int(val.replace(" ",""),16)
         if val<=4294967295:
            if val<=2147483647:
               val=val
            else:
               val=-4294967295+val

      if datatype[:3] == "14.": #32bit IEEE 754 floating point number
         val=int(val.replace(" ",""),16)
         val= unpack('f',pack('I',val))[0]

      if datatype[:3] =="16.": #String
         val=val.replace(" ","")
         if len(val)/2==14:
            phrase=""
            for i in range(len(val)/2):
               phrase=phrase+ chr(int(val[0:2],16))
            val=val[2:]
            val=phrase

      if datatype == "20.102": #heating mode (comfort/standby/night/frost) 
         val=int(val.replace(" ",""),16)
         if val==20 or val==28:
            val="HVACnormal" #1
         if val==19 or val==24:
            val="HVACeco" #3
         if val==7:
            val="HVACnofreeze" #4
         if val==26:
            val="HVACstop" #2

      if datatype == "DT_HVACEib":
         val=int(val.replace(" ",""),16)
         print "reception DT_HVAC %s" %val
         value="DT_HVACEib"
         if val==2 or val==19:
            value="HVACeco"
         if val==3 or val==20:
            value="HVACnormal"
         if val==4 or val==17:
            value="HVACnofreeze"
         val=value
      return val 


def encodeKNX(datatype,val):

   valeur=val
   if datatype =="1.001":
      data_type="s"
      if val == "on" or val == "1":
         valeur=1
      if val == "off" or val == "0":
         valeur=0

   if datatype == "1.008":
      data_type="s"
      if val == "up" or val == "0":
         valeur=0
      if val == "down" or val ==1:
         valeur=1

   if datatype =="3.007":
      data_type="s"
      if val=="dim+":
         valeur="9"
      if val == "dim-":
         valeur="1"
      if val=="stop+":
         valeur=8
      if val=="stop-":
         valeur=0

   if datatype =="3.008":
      data_type="s"
      if val=="downstep":
         valeur="9"
      if val == "upstep":
         valeur="1"
      if val=="downstop":
         valeur=8
      if val=="upstop":
         valeur=0

   if datatype[:2] =="5." and datatype!="5.001" and datatype!="5.003": #8bit unsignet int 
      val=int(val)
      data_type="l"
      if val>=0 and val<=255:
         val=hex(val)[2:]
         valeur=""
         for i in range(len(val)/2):
            valeur=valeur+" "+val[0:2]
         valeur=valeur.strip()

   if datatype == '5.001':
      data_type="l"
      print 'envoie d un pourcent'
      if val<>"None":
         val = int(valeur)*255/100
         valeur=hex(val)[2:]
      else:
         valeur=0

   if datatype == "5.003":
      data_type="l"
      print 'envoie d un angle %s' %val
      val=int(val)
      if val<=360 and val>=0:
         val=int(val)*255/360
         print val
         valeur=hex(val)

   if datatype[:2] == "6.": #8bit signed integer (EIS14) 
      data_type="l"
      val=int(val)
      print "|%s|" %val
      if val<=127 and val>=-128:
         if val<0:
            val=256+val
         valeur=hex(val)[2:]	

   if datatype[:2] == "7.": #16bit unsigned integer (EIS14) 
      data_type="l"
      val=int(val)
      if val>=0 and val<=65535:
         val=hex(val)[2:]
         valeur=""
         if len(val)<4:
            for i in range(4-len(val)):
               val="0"+val
         valeur=val[:2]+" "+val[2:4]                      
         print "Valeur 16 bit unsigned val=|%s|" %valeur

   if datatype[:2] == "8.": #16bit signed integer (EIS14) 
      data_type="l"
      val=int(val)
      if val<=32767 and val>=-32768:
         if val<0:
            val=65536+val
      val=hex(val)[2:]
      valeur=val[:2]+" "+val[2:4]

   if datatype[:2] == "9.": #16bit floating signed (EIS14) 
      data_type="l"
      val=val.replace(",",".")
      signe="plus"
      val=float(val)
      if val<0:
         val=abs(val)
         signe="moin"
      tmp = int(100 * abs(val))
      for y in range(0, 15):
         x = tmp >> y
         if x >= 0 and x < 2048:
            break
      if signe=="moin":
         x=4096-x
      binaireX=bin(x)[2:]
      binairey=bin(y)[2:]
      if len(binaireX)<=12:
         for i in range(12-len(binaireX)):
            binaireX="0"+binaireX
      if len(binairey)<>4:
         for i in range(4-len(binairey)):
            binairey="0"+binairey
      valeur=str(binaireX)[0:1]+" "+str(binairey)+" "+str(binaireX)[1:]
      valeur=valeur.replace(" ","")
      valeur=int(valeur,2)
      valeur=hex(valeur)[2:]
      if len(valeur)<4:
         for i in range(4-len(valeur)):
            valeur="0"+valeur
      valeur=valeur[:2]+" "+valeur[2:4]

   if datatype == "10.001": #time
      data_type="l"
      hour=int(strftime('%H',localtime()))
      minute=int(strftime('%M',localtime()))
      seconde=int(strftime('%S',localtime()))
      weekday=int(strftime('%w',localtime()))
      hour=bin(hour)[2:]
      minute=hex(minute)[2:]
      weekday=bin(weekday)[2:]
      seconde=hex(seconde)[2:]
      if len(hour)<5:
         for i in range(5-len(hour)):
            hour="0"+hour
      if len(weekday)<3:
         for i in range(3-len(weekday)):
            weekday="0"+weekday
      if len(minute)<2:
         minute="0"+minute
      if len(seconde)<2:
         seconde="0"+seconde
      dayhour=weekday+hour
      dayhour=hex(int(dayhour,2))[2:]
      valeur=str(dayhour)+" "+str(minute)+" "+str(seconde)

   if datatype == "11.001": #Date
      data_type="l"
      dayofmounth=hex(int(strftime('%d',localtime())))[2:]
      mounth=hex(int(strftime('%m',localtime())))[2:]
      years=hex(int(strftime('%y',localtime())))[2:]
      if len(dayofmounth)<2:
         dayofmounth="0"+dayofmounth
      if len(mounth)<2:
         mounth="0"+mounth
      if len(years)<2:
         years="0"+years
      valeur=dayofmounth+" "+mounth+" "+years


   if datatype[:3] == "12.": #32bit unsigned integer (EIS14) 
      data_type="l"
      val=int(val)
      if val>=0 and val<=4294967295:
         val=hex(val)[2:]
         if len(val)<8:
            for i in range(8-len(val)):
               val="0"+val                    
         valeur=val.strip()
         valeur=valeur[:2]+" "+valeur[2:4]+" "+valeur[4:6]+" "+valeur[6:8]
  
   if datatype[:3] == "13.": #32bit signed integer
      data_type="l"
      val=int(val)
      if val<=2147483647 and val>=-2147483648:
         if val<0:
            val=4294967295+val
         val=hex(val)[2:]
         if len(val)<8:
            for i in range(8-len(val)):
               val="0"+val
         valeur=val.strip()
         valeur=valeur[:2]+" "+valeur[2:4]+" "+valeur[4:6]+" "+valeur[6:8]
     
   if datatype == "14.001": #IEE754 floating
      data_type="l"
      print "valeur 14.001 %s" %val
      val=float(val)
      valeur=hexlify(pack('>f',val))
      print "IEE754 %s" %valeur
      if len(valeur)==8:
         valeur=valeur[0:2]+" "+valeur[2:4]+" "+valeur[4:6]+" "+valeur[6:8]

   if datatype == "16.000": #string
      data_type="l"
      codage=""
      text=val
      for j in range(int(len(val)/14)+1):
         val=text[j*14:j*14+14]
         codage=""
         if len(val)<=14:
            for j in range(len(val)):
               codage=codage+" "+hex(ord(val[j:j+1]))[2:]
            if len(val)<14:
               for j in range(14-len(val)):
                  codage=codage+" 00"
            print codage
            command="groupwrite ip:127.0.0.1 %s %s" %(cmdadr,codage)
            subp2=subprocess.Popen(command,shell=True)
      type_cmd="None" 

   if datatype == "20.102": #HVAC Mode
      data_type="l"
      if val == "1" or val == "HVACnormal":
         valeur=1
      if val == "2" or val == "HVACstop":
         valeur=2
      if val == "3" or val == "HVACeco":
         valeur=3
      if val == "4" or val == "HVACnofreeze":
         valeur=4

   if datatype == "DT_HVACEib": #Datapoint type for TB042
      data_type="l"
      if val == "4" or val == "HVACnofreeze":
         valeur=4
      if val == "3" or val == "HVACeco":
         valeur="2"
      if val == "1" or val == "HVACnormal":
         valeur="3"
      if val == "2" or val == "HVACstop":
         valeur=4

   value=(data_type,valeur)
   return value



class KNXException(Exception):
    """
    KNX exception
    """

    def __init__(self, value):
        Exception.__init__(self)
        self.value = value

    def __str__(self):
        return repr(self.value)


class KNX:
   

    def __init__(self, log, callback):
        self._log = log
        self._callback = callback
        self._ser = None


    def open(self):
        """ open
            @param device :
        """
#        print("Lancement de EIBD")
        # device example : "ipt:192.168.0.148"
#        command = "eibd -i -d -D %s" 
#        print("lancement de la commande: %s" %command)
        ##subp = subprocess.Popen(command, shell=True)
        ##self.eibd_pid = subp.pid


    def close(self):
        """ close t
        """
        #subp = subprocess.Popen("kill -9 %s" % self.eibd_pid, shell=True)
        subp = subprocess.Popen("pkill groupsock*", shell=True)
        print "pkill groupsock"
        # TODOD : add check and kill -9 if necessary

    def listen(self):
        command = "groupsocketlisten ip:127.0.0.1"
        self.pipe = subprocess.Popen(command,
                     shell = True,
                     bufsize = 1024,
                     stdout = subprocess.PIPE
                     ).stdout
        self._read = True                                                       

        while self._read:
            data = self.pipe.readline()
            if not data:
                break
            self._callback(data)

    def stop_listen(self):
        print("arret du listen")
        self._read = False

if __name__ == "__main__":                                                      
    device = "ipt:192.168.0.148"                                                        
    obj = KNX(None, decode)                                                     
    obj.open(device)
    obj.listen()           


    
       


