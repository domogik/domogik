#!/usr/bin/python
# -*- encoding:utf-8 -*-

# Copyright 2008 Domogik project

# This file is part of Domogik.
# Domogik is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# Domogik is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with Domogik.  If not, see <http://www.gnu.org/licenses/>.

# Author: Maxence Dunnewind <maxence@dunnewind.net>

# $LastChangedBy: mschneider $
# $LastChangedDate: 2009-02-02 23:07:23 +0100 (lun 02 fév 2009) $
# $LastChangedRevision: 321 $

from xPLAPI import *
from configloader import Loader

class Condition():
    def __init__(self, cond1=None, cond2=None):
        self.cond1 = cond1
        self.cond2 = cond2
        
    def run(self, statedic):
        raise NotImplementedException
        
    def parse(self,listelem):
        res1 = self.cond1.parse(listelem)
        res2 = self.cond2.parse(listelem)
        for k in res2:
            res1[k].update(res2[k])
        return res1

#####
# Classes représentants les conditions (noeuds de l'arbre)
#####
class OR(Condition):
    def __init__(self, cond1, cond2):
        Condition.__init__(self, cond1, cond2)
    
    def run(self, statedic):
        return self.cond1.run(statedic) or self.cond2.run(statedic)
        
        
class AND(Condition):
    def __init__(self, cond1, cond2):
        Condition.__init__(self, cond1, cond2)
    
    def run(self, statedic):
        return self.cond1.run(statedic) and self.cond2.run(statedic)
        
class NOT(Condition):
    def __init__(self, cond1):
        Condition.__init__(self, cond1)
    
    def run(self, statedic):
        return not self.cond1.run(statedic)
    
    def parse(self, listelem):
        return self.cond1.parse(listelem)
        
#####
# Classes représentant les feuilles (conditions de temps ou d'état)
#####
class timeCond(Condition):
    def __init__(self,year, month, day, daynumber, hour, minute):
        self.year = year
        self.month = month
        #...
        self.minute = minute
        
    def run(self, statedic):
        pass
        #long à coder :p
        #TODO : chaque variable peut etre un entier, un interval (liste), une liste d'intervales ou la chaine '*'
    
    def parse(self, listelem):
        res = {'year':None, 'month':None, 'day':None, 'daynumber':None, 'hour':None, 'minute':None}
        listelem['time'] = res
        return listelem

class stateCond(Condition):
    def __init__(self, technology, item_name, operator, value):
        self.technology = technology
        self.item_name = item_name
        self.operator = operator
        self.value = value
        
    def run(self, statedic):
        if (isinstance(self.value, int):
            return eval("%s %s %s" % (int(statedic[self.technology][self.item_name]), self.operator, self.value))
        else
            return eval("'%s' %s '%s'" % (statedic[self.technology][self.item_name], self.operator, self.value))
    
    def parse(self, listelem):
        if not listelem.has_key(self.technology):
            listelem[self.technology] = {}
        listelem[self.technology][self.item_name] = None
        return listelem

####
# methodes gérant la récup des infos
####
class ListenerBuilder():
    
    def __init__(self, listitems, expr):
        self.listitems = listitems
        loader = Loader('trigger')
        config = loader.load()[1]
        self.__myxpl = Manager(config["address"],port = config["port"], source = config["source"])
        self.__expr = expr

        #We should try/catch this bloc in case of undefined method
        #Anyway, if they're not defined, needed value will never be updated,
        #So we prefer raise an exception now
        for k in listitems:
            call = "self.build%slistener(listitems[k])" % k.lower()
            eval(call)

    def hasAllNeededValue(self):
        all = True
        for k in self.listitems:
            for j in self.listitems[k]:
                if self.listitems[k][j] == None:
                    all = False
        if all:
            r = eval(self.__expr+".run(self.listitems)")
            print "Result evaluated to : " + str(r)

    def updateList(self, k1, k2, v):
        self.listitems[k1][k2] = v
        self.hasAllNeededValue()

    def buildx10listener(self, items):
        for i in items:
            Listener(lambda mess: self.updateList('x10',mess.get_key_value('device'), mess.get_key_value('command')) , self.__myxpl, {'schema':'x10.basic','device':i,'type':'xpl-cmnd'})

if __name__ == "__main__":
    #Petits tests
    state1 = "stateCond('x10','a1','==','on')"
    state2 = "stateCond('1wire','X23329500234','<','20')"
    state3 = "stateCond('x10','c3','==','off')"
    time1 = "timeCond(2008,'*',[25-30],2,00,10)"
    expr1 = "AND(%s, OR(%s, %s))" % (state1, time1, state2)

    liste = {}
    print "****************  Test du parsing  *******************"
    print "Parsing de l'expression : %s" % expr1
    print eval(expr1+".parse(liste)")

    print "**************** Test des listeners *******************"
    expr2 = "AND(%s, %s)" % (state1, state3)
    print "Parsing de l'expression : %s" % expr2
    liste = {}
    parsing =  eval(expr2+".parse(liste)")
    print parsing
    l = ListenerBuilder(parsing, expr2)

