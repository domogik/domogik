#!/usr/bin/python
from domogik.xpl.common.helper import Helper
from domogik.xpl.common.helper import HelperError
from domogik.common import logger
from domogik.xpl.lib.zwave import *
from time import sleep
from threading import Event


class Zwave(Helper):
    def __init__(self):
	self._event = Event()
        self.message = []
        self.commands = \
            { "find" :
                {
                "cb" : self.find,
                "desc" : "Show all nodes found on Z-wave network",
                },
              "info" :
                {
                "cb" : self.info,
                "desc" : "Show node info",
                "min_args" : 1,
                "usage" : "Show info for specified node <node id>",
                }
            }
        log = logger.Logger('zwave-helper')
        self._log = log.get_logger()
	self._log.error("WAAARRRRNIIIIING")
        device = '/dev/ttyUSB0'
        self.myzwave = zwave(device, '115200', self._cb, self._log)
	self._log.error("juste avant le start")
        self.myzwave.start()
                
    def find(self, args = None):
        self._log.error("Envoie de la trame")
        self.myzwave.send('Network Discovery')
        self._log.error("Trame envoyee, wait")
        self._event.wait()
        self._log.error("cb fini retour dans le find")
        self._event.clear()
        self.log.error("stopage du zwave")
        self.myzwave.stop()
        self._log.error("zwave stoppe")
        return self.message

    def info(self, args = None):
        node = args [0]
        self.myzwave.send('Info', node)
        self._event.wait()
        self._event.clear()
        self.myzwave.stop()
        return self.message
        
    def _cb(self, data):
        self.log.error("cb")
        if 'Info' in data:
            self.message.append(data['Info'])
            self._event.set()
        elif 'Find' in data:
            self._log.error("on entre dans le Find et on ajoute la data au message")
            self.message.append(data['Find'])
            self._log.error("event set")
            self._event.set()


MY_CLASS = {"cb" : Zwave}

