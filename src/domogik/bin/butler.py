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

Component purpose
=================

This component is the butler, your domogik assistant

Implements
==========


@author: Fritz SMH <fritz.smh at gmail.com>
@copyright: (C) 2007-2015 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

import traceback
from argparse import ArgumentParser
from threading import Thread

from domogik.common.configloader import Loader, CONFIG_FILE
from domogik.xpl.common.plugin import XplPlugin
from domogik.common.plugin import Plugin
from domogik.butler.rivescript import RiveScript
#from domogikmq.reqrep.worker import MQRep
from domogikmq.message import MQMessage
from domogikmq.pubsub.subscriber import MQAsyncSub
from domogikmq.pubsub.publisher import MQPub
#import zmq
import os
from subprocess import Popen, PIPE
import time
import unicodedata



BRAIN_PKG_TYPE = "brain"
MINIMAL_BRAIN = "{0}/../butler/brain_minimal.rive".format(os.path.dirname(os.path.abspath(__file__)))
RIVESCRIPT_DIR = "rs"
RIVESCRIPT_EXTENSION = ".rive"

SEX_MALE = "male"
SEX_FEMALE = "female"
SEX_ALLOWED = [SEX_MALE, SEX_FEMALE]

class Butler(Plugin, MQAsyncSub):
    """ Butler component

        TODO : 
        * /quit /reload commands
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

        ### MQ
        # MQ publisher
        #self._mq_name = "interface-{0}.{1}".format(self._name, self.get_sanitized_hostname())
        self._mq_name = "butler"
        #self.zmq = zmq.Context()
        self.pub = MQPub(self.zmq, self._mq_name)

        # subscribe the MQ for interfaces inputs
        MQAsyncSub.__init__(self, self.zmq, self._name, ['interface.input'])


        ### Configuration elements
        try:
            cfg = Loader('butler')
            config = cfg.load()
            conf = dict(config[1])

            self.lang = conf['lang']
            self.butler_name = conf['name']
            self.butler_sex = conf['sex']
            if self.butler_sex not in SEX_ALLOWED:
                self.log.error(u"The butler sex configured is not valid : '{0}'. Expecting : {1}".format(self.butler_sex, SEX_ALLOWED))
                self.force_leave()
                return
       
        except:
            self.log.error(u"Error while reading the configuration file '{0}' : {1}".format(CONFIG_FILE, traceback.format_exc()))
            self.force_leave()
            return
        # user name (default is 'localuser')
        # this is not used for now on Domogik side
        self.user_name = "localuser"

        ### Prepare the brain
        # - validate packages

        # Start the brain :)
        self.brain = RiveScript(utf8=True)

        # set rivescript variables

        # load the brain
        self.load_all_brain()

        # Configure bot variables
        self.brain.set_variable("name", self.butler_name)
        self.brain.set_variable("fullname", self.butler_name)
        self.brain.set_variable("sex", self.butler_sex)

        print(u"*** Welcome in {0} world, your digital assistant! ***".format(self.butler_name))
        print(u"You may type /quit to let {0} have a break".format(self.butler_name))


        ### Interactive mode
        if self.options.interactive:
            self.log.info(u"Launched in interactive mode : running the chat!")
            # TODO : run as a thread
            #self.run_chat()
            thr_run_chat = Thread(None,
                                  self.run_chat,
                                  "run_chat",
                                  (),
                                  {})
            thr_run_chat.start()
        else:
            self.log.info(u"Not launched in interactive mode")
        

        ### TODO
        #self.add_stop_cb(self.shutdown)

        self.log.info(u"Butler initialized")
        self.ready()


    def on_mdp_request(self, msg):
        """ Handle Requests over MQ 
            @param msg : MQ req message
        """
        try:
            ### rivescript files detail
            if msg.get_action() == "butler.scripts.get":
                self.log.info(u"Scripts request : {0}".format(msg))
                self._mdp_reply_butler_scripts(msg)
            ### rivescript files detail
            elif msg.get_action() == "butler.reload.do":
                self.log.info(u"Reload brain request : {0}".format(msg))
                self._mdp_reply_butler_reload(msg)
        except:
            self.log.error(u"Error while processing MQ message : '{0}'. Error is : {1}".format(msg, traceback.format_exc()))
   

    def _mdp_reply_butler_scripts(self, message):
        """ Send the raw content for the brain parts over the MQ
        """

        # TODO : handle choice of the client in the req message

        msg = MQMessage()
        msg.set_action('butler.scripts.result')
        for client_id in self.brain_content:
            msg.add_data(client_id, self.brain_content[client_id])
        self.reply(msg.get())


    def _mdp_reply_butler_reload(self, message):
        """ Reload the brain 
        """
        msg = MQMessage()
        msg.set_action('butler.reload.result')
        try:
            self.load_all_brain()
            msg.add_data(u"status", True)
            msg.add_data(u"reason", "")
        except:
            msg.add_data(u"status", False)
            msg.add_data(u"reason", "Error while reloading brain parts : {0}".format(traceback.format_exc()))
        self.reply(msg.get())


    def load_all_brain(self):
        """ Load all the brain parts (included in domogik or in packages)
            and do any other related actions
        """
        try:
            # load the minimal brain
            self.brain_content = {}   # the brain raw content for display in the admin (transmitted over MQ)
            self.log.info(u"Load minimal brain : {0}".format(MINIMAL_BRAIN))
            self.brain.load_file(MINIMAL_BRAIN)

            # load packages for the brain
            self.load_brain_parts()

            # sort replies
            self.brain.sort_replies()
        except:
            self.log.error(u"Error while loading brain : {0}".format(traceback.format_exc()))

    def load_brain_parts(self):
        """ Load the parts of the brain from /var/lib/domogik/domogik_packages/brain_*
        """
        try:
            list = []
            for a_file in os.listdir(self.get_packages_directory()):
                if a_file[0:len(BRAIN_PKG_TYPE)] == BRAIN_PKG_TYPE:
                    self.log.info(u"Brain part found : {0}".format(a_file))
                    client_id = "{0}-{1}.{2}".format(BRAIN_PKG_TYPE, a_file.split("_")[1], self.get_sanitized_hostname())
                    self.brain_content[client_id] = {}
                    rs_dir = os.path.join(self.get_packages_directory(), a_file, RIVESCRIPT_DIR)
                    if os.path.isdir(rs_dir):
                        #self.log.debug(u"The brain part contains a rivescript folder ({0})".format(RIVESCRIPT_DIR))
                        lang_dir = os.path.join(rs_dir, self.lang)
                        if os.path.isdir(lang_dir):
                            self.log.info(u"- Language found : {0}".format(self.lang))
                            # add the brain part to rivescript
                            self.brain.load_directory(lang_dir)
                            # add the files raw data to brain content (to be sent over MQ to the admin)
                            self.brain_content[client_id][self.lang] = {}
                            for a_rs_file in os.listdir(lang_dir):
                                a_rs_file_path = os.path.join(lang_dir, a_rs_file)
                                if os.path.isfile(a_rs_file_path) and a_rs_file[-len(RIVESCRIPT_EXTENSION):] == RIVESCRIPT_EXTENSION:
                                    try:
                                        import codecs
                                        file = codecs.open(a_rs_file_path, 'r', 'utf-8')
                                        file_content = file.read()
                                        content = u"{0}".format(file_content)
                                    except:
                                        content = u"Error while reading file '{0}'. Error is : {1}".format(a_rs_file_path, traceback.format_exc())
                                        self.log.error(content)
                                    self.brain_content[client_id][self.lang][a_rs_file] = content
                              
        except:
            msg = "Error accessing packages directory : {0}. You should create it".format(str(traceback.format_exc()))
            self.log.error(msg)


    def process(self, query):
        """ Process the input query by calling rivescript brain
            @param query : the text query
        """
        try:
            self.log.debug(u"Before transforming query : {0})".format(query))
            if isinstance(query, str):
                query = unicode(query, 'utf-8')

            # remove non standard caracters
            query = query.replace("'", " ")

            # remove accents
            query = unicodedata.normalize('NFD', query).encode('ascii', 'ignore')

            # process the query
            self.log.debug(u"Before calling Rivescript brain for processing : {0} (type={1})".format(query, type(query)))
            reply = self.brain.reply(self.user_name, query)
            self.log.debug(u"Processing finished. The reply is : {0}".format(reply))
            return reply
        except:
            self.log.error(u"Error while processing query '{0}'. Error is : {1}".format(query, traceback.format_exc()))
            self.log.error(reply)
            self.log.error(type(reply))
            return "Error"


    def shutdown(self):
        """ Shutdown the butler
        """
        pass

    def on_message(self, msgid, content):
        """ When a message is received from the MQ (pub/sub)
        """
        if msgid == "interface.input":
            self.log.info(u"Received message : {0}".format(content))
            print(type(content['text']))

            ### Get response from the brain
            # TODO : do it in a thread and if this last too long, do :
            # 3s : reply "humm..."
            # 10s : reply "I am checking..."
            # 20s : reply "It takes already 20s for processing, I cancel the request" and kill the thread
            #reply = self.brain.reply(self.user_name, content['text'])
            reply = self.process(content['text'])
            print(u"DEBUG REPLY={0}".format(reply))

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

            self.log.info(u"Send response over MQ : media = '{0}', location = '{1}', reply_to = '{2}', text = {3}".format(content['media'], content['location'], content['identity'], reply))
            # publish over MQ
            self.pub.send_event('interface.output',
                                {"media" : content['media'],
                                 "location" : content['location'],
                                 "reply_to" : content['identity'],
                                 "text" : reply})


    def run_chat(self):
        """ Nestor starts to serve his master over the chat
            the chat is really usefull for debugging

            TODO : allow Nestor to connect over irc on demand for test purpose
        """
        # just wait for 2s to have a cleaner output
        #time.sleep(2)
        # start serving for an entire life
        while True:
            msg = raw_input(u"You > ")

            # first, let python handle some system messages
            if msg == '/quit':
                quit()

            # then, let Nestor do his work!!!
            #reply = self.brain.reply(self.user_name, msg)
            reply = self.process(msg)

            # let Nestor answer in the chat
            print(u"{0} > {1}".format(self.butler_name, reply))

            # let Nestor speak
            #tts = u"espeak -p 40 -s 140 -v mb/mb-fr1 \"{0}\" | mbrola /usr/share/mbrola/fr1/fr1 - -.au | aplay".format(reply)
            #tts = u"espeak -p 40 -s 140 -v mb/mb-fr1 \"{0}\" | mbrola /usr/share/mbrola/fr1 - -.au | aplay".format(reply)
            #subp = Popen(tts, shell=True)
            #pid = subp.pid
            #subp.communicate()



if __name__ == "__main__":
    Butler()
