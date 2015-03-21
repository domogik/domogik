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

This plugin manages scenarii, it provides MQ interface

Implements
==========


@author: Fritz SMH <fritz.smh at gmail.com>
@copyright: (C) 2007-2014 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

import traceback
from argparse import ArgumentParser

from domogik.common.plugin import Plugin
from domogik.butler.rivescript import RiveScript
#DELETE#   from domogik.butler.common import *
#from domogikmq.reqrep.worker import MQRep
#from domogikmq.message import MQMessage
from domogikmq.pubsub.subscriber import MQAsyncSub
from domogikmq.pubsub.publisher import MQPub
from zmq.eventloop.ioloop import IOLoop
import zmq
import os


BRAIN_PKG_TYPE = "brain"
EMPTY_BRAIN = "../butler/brain_empty.rive"
RIVESCRIPT_DIR = "rs"

class Butler(Plugin, MQAsyncSub):
    """ Butler component

        TODO : 
        * check docs : 
          * https://github.com/aifr/aifr-docs
        * include existing french brain from https://github.com/aifr/rivescriptfr
        * /quit /reload commands
        * interact with domogik : sensors
        * interact with domogik : commands
    """

    def __init__(self):

        ### Option parser
        parser = ArgumentParser()
        parser.add_argument("-i", 
                          action="store_true", 
                          dest="interactive", 
                          default=False, \
                          help="Butler interactive mode (must be used WITH -f).")

        Plugin.__init__(self, name = 'butler', parser = parser)

        ### Configuration elements
        # TODO : get these elements from the .cfg file
        # default name 
        self.butler_name = "nestor"
        # user name (default is 'localuser')
        self.user_name = "localuser"
        # lang 
        self.lang = 'fr_FR'

        ### Prepare the brain
        # TODO
        # - load packages
        # - validate packages

        # Start the brain :)
        self.brain = RiveScript(utf8=True)

        # set rivescript variables

        # load the minimal brain
        #self.brain.load_directory("../butler/brain_base_{0}".format(self.lang))
        self.brain.load_file(EMPTY_BRAIN)

        # TODO : load packages for the brain
        self.load_brain_parts()

        # TODO : describe this command
        self.brain.sort_replies()

        # Configure bot variables
        self.brain.set_variable("name", self.butler_name)
        self.brain.set_variable("fullname", self.butler_name)

        print("*** Welcome in {0} world, your digital assistant! ***".format(self.butler_name))
        print("You may type /quit to let {0} have a break".format(self.butler_name))

        ### MQ

        # subscribe the MQ for interfaces inputs
        MQAsyncSub.__init__(self, self.zmq, self._name, ['interface.input'])

        # MQ publisher
        self._mq_name = "interface-{0}.{1}".format(self._name, self.get_sanitized_hostname())
        self.zmq = zmq.Context()
        self.pub = MQPub(self.zmq, self._mq_name)


        ### Interactive mode
        if self.options.interactive:
            self.log.info("Launched in interactive mode : running the chat!")
            # TODO : run as a thread
            self.run_chat()
        else:
            self.log.info("Not launched in interactive mode")
        

        ### TODO
        #self.add_stop_cb(self.shutdown)

        self.log.info(u"Butler initialized")
        self.ready()

    def load_brain_parts(self):
        """ Load the parts of the brain from /var/lib/domogik/domogik_packages/brain_*
        """
        try:
            list = []
            for a_file in os.listdir(self.get_packages_directory()):
                if a_file[0:len(BRAIN_PKG_TYPE)] == BRAIN_PKG_TYPE:
                    self.log.info("Brain part found : {0}".format(a_file))
                    rs_dir = os.path.join(self.get_packages_directory(), a_file, RIVESCRIPT_DIR)
                    if os.path.isdir(rs_dir):
                        #self.log.debug("The brain part contains a rivescript folder ({0})".format(RIVESCRIPT_DIR))
                        lang_dir = os.path.join(rs_dir, self.lang)
                        if os.path.isdir(lang_dir):
                            self.log.info("- Language found : {0}".format(self.lang))
                            self.brain.load_directory(lang_dir)
        except:
            msg = "Error accessing packages directory : {0}. You should create it".format(str(traceback.format_exc()))
            self.log.error(msg)


    def shutdown(self):
        """ Shutdown the butler
        """
        pass

    def on_mdp_request(self, msg):
        """ MQ messages reception (req/rep)
        """
        pass

    def on_message(self, msgid, content):
        """ When a message is received from the MQ (pub/sub)
        """
        if msgid == "interface.input":
            self.log.info("Received message : {0}".format(content))

            ### Get response from the brain
            # TODO : do it in a thread and if this last too long, do :
            # 3s : reply "humm..."
            # 10s : reply "I am checking..."
            # 20s : reply "It takes already 20s for processing, I cancel the request" and kill the thread
            reply = self.brain.reply(self.user_name, content['text'])

            ### Prepare response for the MQ
            # All elements that may be added in the request sent over MQ for interface.output
            # * media (irc, audio, sms, ...)
            # * text (from voice recognition)
            # * location (the input element location : this is configured on the input element : kitchen, garden, bedroom, ...)
            # * reply_to (from face recognition)
            
            #self.context = {"media" : "irc",
            #                "location" : "internet",
            #                "reply_to" : content['identity']
            #               }
            #self.context['text'] = reply

            self.log.info("Send response over MQ : media = irc, location = '{0}', reply_to = '{1}', text = {2}".format(content['location'], content['identity'], reply))
            # publish over MQ
            self.pub.send_event('interface.output',
                                {"media" : "irc",
                                 "location" : content['location'],
                                 "reply_to" : content['identity'],
                                 "text" : reply})


    def run_chat(self):
        """ Nestor starts to serve his master over the chat
            the chat is really usefull for debugging

            TODO : allow Nestor to connect over irc on demand for test purpose
        """
        # start serving for an entire life
        while True:
            msg = raw_input("You > ")

            # first, let python handle some system messages
            if msg == '/quit':
                quit()

            # then, let Nestor do his work!!!
            reply = self.brain.reply(self.user_name, msg)

            # let Nestor answer in the chat
            print(u"{0} > {1}".format(self.butler_name, reply))

            # let Nestor speak
            #tts = u"espeak -p 40 -s 140 -v mb/mb-fr1 \"{0}\" | mbrola /usr/share/mbrola/voices/fr1 - -.au | aplay".format(reply)
            #subp = Popen(tts, shell=True)
            #pid = subp.pid
            #subp.communicate()



if __name__ == "__main__":
    Butler()
