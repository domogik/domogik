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

@author: Maxence Dunnewind <maxence@dunnewind.net>
@copyright: (C) 2007-2013 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

from domogik.scenario.actions.abstract import AbstractAction
from domogik.common.database import DbHelper


class SetVariableAction(AbstractAction):
    """ Set a variable
    """

    def __init__(self, log=None, params=None):
        AbstractAction.__init__(self, log)
        self.set_description("Set")
        self._db = DbHelper()

    def do_action(self, local_vars):
        self._log.info("Variable name={0}".format(self._params['name']))
        self._log.info("Variable value={0}".format(self._params['value']))

        # if value is a sensor, get its last value (current) value
        # 2016-01-19 22:49:29,666 domogik-scenario INFO Variable name=thename
        # 2016-01-19 22:49:29,667 domogik-scenario INFO Variable value={u'type': u'sensor.SensorTest.39', u'id': u'8G446-[l)(cP30]-YZEF'}
        the_name = self._params['name']
        val = self._params['value']
        the_value = "null"   # for an appropriate display value in real usage
        if val['type'].startswith("sensor.SensorTest."):
            sen_id = val['type'].split(".")[2]
            self._log.debug("Variable value comes from the sensor : id='{0}'".format(sen_id))
            # get info from db
            with self._db.session_scope():
                sensor = self._db.get_sensor(sen_id)
                if sensor is not None:
                    the_value = sensor.last_value
                 
            self._log.info("Variable value (from sensor)={0}".format(the_value))

        # TODO : non sensor values!

        # set the variable
        if local_vars == None:
            local_vars = {}
        local_vars["{0}".format(the_name)] = the_value
        self._log.info("Updated local variables : '{0}'".format(local_vars))


    def get_expected_entries(self):
        return {'name': {'type': 'string',
                            'description': 'variable',
                            'default': ''},
                'value': {'type': 'external',
                            'description': 'to',
                            'default': ''}
               }
