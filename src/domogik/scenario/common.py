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

Manage user triggers and conditions

Implements
==========

- Condition.__init__(self, cond1=None, cond2=None)
- Condition.run(self, statedic)
- Condition.parse(self, listelem)
- TimeCond.__init__(self, minute, hour, day, month, daynumber, year)
- TimeCond._check_time(self, timeunit, value)
- TimeCond._check_time_int(self, unit, value)
- TimeCond._check_time_tuple(self, unit, value)
- TimeCond._check_time_list(self, unit, value)
- TimeCond._check_time_str(self, unit, value)
- TimeCond.run(self, statedic)
- TimeCond.parse(self, listelem)
- StateCond.__init__(self, technology, item_name, operator, value)
- StateCond.run(self, statedic)
- StateCond.parse(self, listelem)
- ListenerBuilder.__init__(self, listitems, expr)
- ListenerBuilder.hasAllNeededValue(self)
- ListenerBuilder.updateList(self, k1, k2, v)
- ListenerBuilder.buildx10listener(self, items)
- ListenerBuilder.buildtimelistener(self, items)
- ListenerBuilder._parsetimeupdate(self, mess)
- main()

@author: Maxence Dunnewind <maxence@dunnewind.net>
@copyright: (C) 2007-2012 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

from domogik.xpl.common.xplconnector import Listener
from domogik.xpl.common.plugin import XplPlugin
from domogik.xpl.common.xplmessage import XplMessage
from domogik.common.configloader import Loader
from domogik.common import logger

class TimeCond:
    '''
    Implementation of the time condition
    This allows user to describe time periods like cron
    '''

    def __init__(self, minute, hour, day, month, daynumber, year):
        '''
        Create a time condition
        Each param can be :
        * an integer (eg : 6, 9, 12)
        * a tuple (eg : (3,9)) : repesents an interval (here between 3 and 9)
        * a list (eg : [4,6,9])
        * a list of tuple (eg : [(4,9),(18,22)] : union of intervals
        * a string (eg : '*', '*/8') : '*' = always, '*/X' = every X time unit
        @param year
        @param month
        @param day
        @param daynumber : 0 - 6 for Monday - Sunday
        @param hour
        @param minute
        '''
        self.year = year
        self.month = month
        self.day = day
        self.hour = hour
        self.minute = minute
        self.daynumber = daynumber
        l = logger.Logger('trigger')
        self._log = l.get_logger('trigger')

    def _check_time(self, timeunit, value):
        '''
            Check the timeunit value
            @param timeunit Can be one of 'year','month','day','daynumber',
                    'hour','minute'
            @param value : the value to check
        '''
        if timeunit not in ['year', 'month', 'day', 'daynumber', 'hour',
                'minute']:
            raise ValueError

        this_unit = eval("self." + timeunit)
        clas = str(this_unit.__class__).split("'")[1]
        value = clas + "('%s')" % value if clas == "int" or clas == "str" \
                else value
        this_unit = clas + "('%s')" % this_unit if clas == "int" or \
                clas == "str" else this_unit
        call = ("self._check_time_" + clas +"(%s,%s)"% (this_unit, value))
        return eval(call)

    ### Functions to check 'time equality' for each used type

    #Int
    def _check_time_int(self, unit, value):
        '''
        Check time equality between to integers
        @param unit : 'value' of the item in the condition
        @param value : value catched by the system
        '''
        return unit == int(value)

    #tuple : represent an interval
    def _check_time_tuple(self, unit, value):
        '''
        Check if value is in the interval described by the tuple
        @param unit : 'value' of the item in the condition (a tuple)
        @param value : value catched by the system
        '''
        return int(value) in range(unit[0], unit[1] + 1)

    #list
    def _check_time_list(self, unit, value):
        '''
        @param unit can be : a list of int => check if value is in the list
                             a list of tuple => expand each tuple to a list
        @param value : value catched by the system
        '''
        if isinstance(unit[0], tuple):
            return any([_check_time_tuple(u, value) for u in unit])
        else:
            return value in unit

    #string
    def _check_time_str(self, unit, value):
        '''
        @param unit can be  '*' or '*/x'
                            '*' => always true
                            '*/x' => value % x == 0
        @param value : value catched by the system
        '''
        if unit == '*':
            return True
        elif unit.startswith('*/'):
            return (int(value) % int(unit.split('/')[1])) == 0
        else:
            self._log.error('Bad time format %s' % unit)

    ### And of functions for evaluation
    def run(self, statedic):
        # chaque variable peut etre un entier, un interval (tuple), une liste
        # d'intervales ou la chaine '*' ou '*/x'
        return all([self._check_time(t, statedic['time'][t]) for t in [
                'year', 'month', 'day', 'daynumber', 'hour', 'minute']])

    def parse(self, listelem):
        res = {'year': None, 'month': None, 'day': None, 'daynumber': None,
                'hour': None, 'minute': None}
        listelem['time'] = res
        return listelem


class StateCond:
    '''
    Implementation of the state condition
    This allows user to describe a condition on any item of the system
    '''

    def __init__(self, technology, item_name, operator, value):
        '''
        @param technology : technolgy of the item (eg : x10, 1wire, etc ...)
        @param item_name : name of the item (eg: A1 for x10, 10B037A5010800DC
        for 1wire)
        @param operator : any comparison operator that python recognize
        (==, <, <=, =>, >, !=)
        @param value : the value to test
        '''
        self.technology = technology
        self.item_name = item_name
        self.operator = operator
        self.value = value

    def run(self, statedic):
        if isinstance(self.value, int):
            return eval("%s %s %s" % (
                    int(statedic[self.technology][self.item_name]),
                    self.operator, self.value))
        else:
            return eval("'%s' %s '%s'" % (
                    statedic[self.technology][self.item_name],
                    self.operator, self.value))

    def parse(self, listelem):
        if self.technology not in listelem:
            listelem[self.technology] = {}
        listelem[self.technology][self.item_name] = None
        return listelem

####
# Methods to catch informations
####

class ListenerBuilder(XplPlugin):
    '''
    Class to parse an expression and create appropriated listener
    '''

    def __init__(self, listitems, expr):
        '''
        @param listitems a dictionnary discribing items used in the condition
        @param expr : the condition
        '''
        XplPlugin.__init__(self, 'dbmgr')
        self._log = self.get_my_logger()
        self.listitems = listitems
        loader = Loader('trigger')
        config = loader.load()[1]
        self.__expr = expr

        #We should try/catch this bloc in case of undefined method
        #Anyway, if they're not defined, needed value will never be updated,
        #So we prefer raise an exception now
        for k in listitems:
            call = "self.build%slistener(listitems[k])" % k.lower()
            eval(call)

    def hasAllNeededValue(self):
        '''
        Check if all the value used in the condition have been catched by
        listeners, then evaluate the expression
        '''
        all = True
        for k in self.listitems:
            for j in self.listitems[k]:
                if self.listitems[k][j] == None:
                    all = False
        if all:
            r = eval(self.__expr+".run(self.listitems)")

    def updateList(self, k1, k2, v):
        '''
        Update the list of items with provided value
        @param k1 : technology
        @param k2 : name of the item
        @param v : new value of the item
        '''
        self._log.debug('updateList')
        self.listitems[k1][k2] = v
        self.hasAllNeededValue()

    def buildx10listener(self, items):
        '''
        Create listener for x10 elements
        @param items : items to add listener for
        '''
        for i in items:
            self._log.debug("New  x10 listener created")
            Listener(lambda mess: self.updateList('x10',
                    mess.data['device'],
                    mess.data['command']),
                    self._myxpl,
                    {'schema': 'x10.basic', 'device': i, 'xpltype': 'xpl-cmnd'})

    def buildtimelistener(self, items):
        '''
        Create listener for time conditions
        '''
        self._log.debug("New time listener created")
        Listener(self._parsetimeupdate, self._myxpl,
                {'schema': 'datetime.basic', 'xpltype': 'xpl-trig'})

    def _parsetimeupdate(self, mess):
        '''
        Parse the time received in a message and call updateList()
        '''
        self._log.debug("Time update")
        dt = mess.data['format1']
        pars = {
            'year': dt[0:4],
            'month': dt[4:6],
            'day': dt[6:8],
            'daynumber': dt[12],
            'hour': dt[8:10],
            'minute': dt[10:12],
        }
        for p in pars:
            self.updateList('time', p, pars[p])


def main():
    '''
    Starts the trigger
    '''
    #Petits tests
    state1 = "StateCond('x10','a1','==','on')"
    state2 = "StateCond('1wire','X23329500234','<','20')"
    state3 = "StateCond('x10','c3','==','off')"
    time1 = "TimeCond('*/3', 10, (2,15), 02, '*', 2009)"
    expr1 = "AND(%s, OR(%s, %s))" % (state1, time1, state2)

    liste = {}
    print("****************  Test du parsing  *******************")
    print("Parsing de l'expression : %s" % expr1)
    print(eval(expr1+".parse(liste)"))

    print("**************** Test des listeners *******************")
    expr2 = "AND(%s, %s)" % (state1, time1)
    #expr2 = "AND(%s, OR(%s, %s))" % (state1, time1, state3)
    print("Parsing de l'expression : %s" % expr2)
    liste = {}
    parsing = eval(expr2+".parse(liste)")
    print(parsing)
    l = ListenerBuilder(parsing, expr2)

if __name__ == "__main__":
    main()
