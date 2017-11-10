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

@author: Fritz SMH <fritz.smh@gmail.com>
@copyright: (C) 2007-2015 Domogik project
@license: GPL(v3)
@organization: Domogik
"""
from __future__ import absolute_import, division, print_function, unicode_literals
from domogik.scenario.actions.abstract import AbstractAction
from domogik.common.configloader import Loader, CONFIG_FILE
from domogik.common.utils import ucode
from domogikmq.pubsub.publisher import MQPub
import zmq
import traceback


class ButlerAction(AbstractAction):
    """ Mock a butler response to send notifications with the butler
    """

    def __init__(self, log=None, params=None):
        AbstractAction.__init__(self, log)
        self.set_description(u"Make the butler say something.")

        ### Butler configuration elements
        try:
            cfg = Loader('butler')
            config = cfg.load()
            conf = dict(config[1])

            self.butler_name = conf['name']
            self.butler_sex = conf['sex']
        except:
            self._log.error(u"ButlerACtion init : error while reading the configuration file '{0}' : {1}".format(CONFIG_FILE, traceback.format_exc()))

        ### MQ
        self._mq_name = "butler"
        self.zmq = zmq.Context()
        self.pub = MQPub(self.zmq, self._mq_name)

    def do_action(self):
        text = self._params['text']

        self._log.info(u"Make the butler say '{0}'. ".format(text))

        # publish over MQ
        data =              {"media" : "*",
                             "location" : "*",
                             "sex" : self.butler_sex,
                             "mood" : None,
                             "reply_to" : None,
                             "identity" : self.butler_name,
                             "text" : text}
        self.pub.send_event('interface.output',
                            data)

    def get_expected_entries(self):
        return {'text': {'type': 'string',
                         'description': 'Text',
                         'default': ''}
               }
