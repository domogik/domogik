#!/usr/bin/python
#-*- encoding:utf-8 *-*

import datetime
import math

class DawnDusk:
    
    def __init__(self):
        pass

    def get_dawn_dusk(self, long, lat, fh):
        k = .0172024
        jm = 308.67
        jl = 21.55
        e = .0167
        ob = .4091
        pi = 3.141593
        dr = pi / 180
        hr = pi / 12
        #Hauteur du soleil au lever et coucher
        ht = (-50 / 60) * dr
        #Longitude et Latitude
        lo = long * dr
        la = lat * dr
        #Recuperation du jour et du mois courant
        today = datetime.date.today()
        jo = today.day
        mo = today.month
        if mo < 3:
            mo = mo + 12
        h = 12 + lo / hr
        #Nombre de jours depuis le premier mars 0
        j = int(30.61 * (mo + 1)) + jo + h / 24 - 123
        #Anomalie et longitude moyenne
        m = k * (j - jm)
        l = k * (j - jl)
        #Longitude réelle
        s = l + 2 * e * math.sin(m) + 1.25 * e * e * math.sin(2 * m)
        #Coordonnees rectangulaires
        x = math.cos(s)
        y = math.cos(ob) * math.sin(s)
        z = math.sin(ob) * math.sin(s)
        #Equation du temps et declinaison
        r = l
        rx = math.cos(r) * x + math.sin(r) * y
        ry = -1 * math.sin(r) * x + math.cos(r) * y
        x = rx
        y = ry
        et = math.atan( y  / x)
        dc = math.atan(z / math.sqrt(1 - z * z))
        #Heure de passage au meridien
        pm = h + fh + et / hr
        hs = int(pm)
        pm = 60 * (pm - hs)
        ms = int(pm)
        pm = 60 * (pm - ms)
        midi = (hs, ms, pm)
        #Angle horaire au lever et coucher du soleil
        cs = (math.sin(ht) - math.sin(la) * math.sin(dc)) / math.cos(la) / math.cos(dc)
        if cs > 1 or cs < -1:
            ah = None
        else:
            if cs == 0:
                ah = pi / 2
            else:
                ah = math.atan(math.sqrt(1 - cs * cs) / cs)
            if cs < 0:
                ah = ah + pi
        #Lever du soleil
        pm = h + fh + (et - ah) / hr
        if pm < 0:
            pm = pm + 24
        hs = int(pm)
        pm = 60 * (pm - hs)
        lever = (hs, pm)
        #Coucher du soleil
        pm = h + fh + (et + ah) / hr
        if pm > 24:
            pm = pm - 24
        hs = int(pm)
        pm = 60 * (pm - hs)
        coucher = (hs, pm)
        return lever, coucher

if __name__ == "__main__":
    dd = DawnDusk()
    l, c = dd.get_dawn_dusk(-01.4046, 48.0653, 1)
    print l
    print c
