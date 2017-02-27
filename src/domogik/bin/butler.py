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
from domogik.butler.rivescript.rivescript import RiveScript
from domogik.butler.brain import LEARN_FILE
from domogik.butler.brain import STAR_FILE
from domogik.butler.brain import clean_input
#from domogikmq.reqrep.worker import MQRep
from domogikmq.message import MQMessage
from domogikmq.reqrep.client import MQSyncReq
from domogikmq.pubsub.publisher import MQPub
import zmq
import json
import os
import sys
from subprocess import Popen, PIPE
import time
import re
import sys
from domogik.common.utils import ucode



BRAIN_PKG_TYPES = ["brain", "plugin"]
MINIMAL_BRAIN = "{0}/../butler/brain_minimal.rive".format(os.path.dirname(os.path.abspath(__file__)))
RIVESCRIPT_DIR = "rs"
RIVESCRIPT_EXTENSION = ".rive"
BRAIN_BASE = "brain_base"

FEATURE_TAG = "##feature##"
SUGGEST_REGEXP = r'\/\* *##suggest##.*\n([\S\s]*?)\*\/'

SEX_MALE = "male"
SEX_FEMALE = "female"
SEX_ALLOWED = [SEX_MALE, SEX_FEMALE]

class Butler(Plugin):
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

        Plugin.__init__(self, name = 'butler', parser = parser, log_prefix='core_')

        ### MQ
        # MQ publisher
        #self._mq_name = "interface-{0}.{1}".format(self._name, self.get_sanitized_hostname())
        self._mq_name = "butler"
        #self.zmq = zmq.Context()
        self.pub = MQPub(self.zmq, self._mq_name)

        # subscribe the MQ for interfaces inputs
        self.add_mq_sub('interface.input')
        # devices updates
        self.add_mq_sub('device.update')


        ### Configuration elements
        try:
            cfg = Loader('butler')
            config = cfg.load()
            conf = dict(config[1])

            self.lang = conf['lang']
            self.butler_name = conf['name']
            self.log.debug(u"The butler configured name is '{0}'".format(self.butler_name))
            self.butler_name_cleaned = clean_input(conf['name'])
            self.log.debug(u"The butler cleaned name is '{0}'".format(self.butler_name_cleaned))
            self.butler_sex = conf['sex']
            self.butler_mood = None
            if self.butler_sex not in SEX_ALLOWED:
                self.log.error(u"Exiting : the butler sex configured is not valid : '{0}'. Expecting : {1}".format(self.butler_sex, SEX_ALLOWED))
                self.force_leave()
                return
       
        except:
            self.log.error(u"Exiting : error while reading the configuration file '{0}' : {1}".format(CONFIG_FILE, traceback.format_exc()))
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

        # Configure bot variables
        # all must be lower case....
        self.log.info(u"Configuring name and sex : {0}, {1}".format(self.butler_name_cleaned.lower(), self.butler_sex.lower()))
        self.brain.set_variable(u"name", self.butler_name_cleaned.lower())
        self.brain.set_variable(u"fullname", self.butler_name.lower())
        self.brain.set_variable(u"sex", self.butler_sex.lower())

        # set the PYTHONPATH
        sys.path.append(self.get_libraries_directory())

        # load the brain
        self.brain_content = None
        self.learn_content = None
        self.not_understood_content = None
        self.load_all_brain()

        # shortcut to allow the core brain package to reload the brain for learning
        self.brain.reload_butler = self.reload

        # shortcut to allow the core brain package to do logging and access the devices in memory
        self.brain.log = self.log
        self.brain.devices = [] # will be loaded in self.reload_devices()


        # history
        self.history = []
 
        # load all known devices
        self.reload_devices()

        self.log.info(u"*** Welcome in {0} world, your digital assistant! ***".format(self.butler_name))

        # for chat more only
        #self.log.info(u"You may type /quit to let {0} have a break".format(self.butler_name))


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


    def reload_devices(self):
        """ Load or reload the devices list in memory to improve the butler speed (mainly for brain-base package usage)
        """
        nb_try = 0
        max_try = 5
        interval = 5
        ok = False
        while nb_try < max_try and ok == False:
            nb_try += 1
            self.log.info(u"Request the devices list over MQ (try {0}/{1})...".format(nb_try, max_try))
            try:
                cli = MQSyncReq(zmq.Context())
                msg = MQMessage()
                msg.set_action('device.get')
                str_devices = cli.request('admin', msg.get(), timeout=10).get()[1]
                self.devices = json.loads(str_devices)['devices']
                self.log.info(u"{0} devices loaded!".format(len(self.devices)))
                self.brain.devices = self.devices
                ok = True
            except:
                self.log.warning(u"Error while getting the devices list over MQ. Error is : {0}".format(traceback.format_exc()))
                self.devices = []
            if ok == False:
                time.sleep(interval)    # TODO : improve with a wait ??

        if ok == False:
            self.brain.devices = []
            self.log.error(u"Error while getting the devices list over MQ after {0} attemps!!!!".format(nb_try))


    def on_mdp_request(self, msg):
        """ Handle Requests over MQ 
            @param msg : MQ req message
        """
        try:
            ### discuss over Req/Rep (used by rest url)
            if msg.get_action() == "butler.discuss.do":
                self.log.info(u"Discuss request : {0}".format(msg))
                self._mdp_reply_butler_discuss(msg)
            ### rivescript files detail
            elif msg.get_action() == "butler.scripts.get":
                self.log.info(u"Scripts request : {0}".format(msg))
                self._mdp_reply_butler_scripts(msg)
            ### rivescript files detail
            elif msg.get_action() == "butler.reload.do":
                self.log.info(u"Reload brain request : {0}".format(msg))
                self._mdp_reply_butler_reload(msg)
            ### history
            elif msg.get_action() == "butler.history.get":
                self.log.info(u"Get butler history : {0}".format(msg))
                self._mdp_reply_butler_history(msg)
            ### features
            elif msg.get_action() == "butler.features.get":
                self.log.info(u"Get butler features : {0}".format(msg))
                self._mdp_reply_butler_features(msg)
        except:
            self.log.error(u"Error while processing MQ message : '{0}'. Error is : {1}".format(msg, traceback.format_exc()))
   

    def _mdp_reply_butler_discuss(self, message):
        """ Discuss over req/rep
            this should NOT be called with a 10 seconds timeout...
        """
        # TODO : merge with the on_message function !!!

        content = message.get_data()
        self.log.info(u"Received message : {0}".format(content))

        self.add_to_history(u"interface.input", content)
        reply = self.process(content['text'])

        # fill empty data
        for elt in ['identity', 'media', 'location', 'sex', 'mood', 'reply_to']:
            if elt not in content:
                content[elt] = None

        # publish over MQ
        data =              {"media" : content['media'],
                             "location" : content['location'],
                             "sex" : self.butler_sex,
                             "mood" : self.butler_mood,
                             "is_reply" : True,
                             "reply_to" : content['source'],
                             "identity" : self.butler_name,
                             "lang" : self.lang,
                             "text" : reply}
        self.log.info(u"Send response over MQ : {0}".format(data))


        msg = MQMessage()
        msg.set_action('butler.discuss.result')
        msg.set_data(data)
        self.reply(msg.get())

        self.add_to_history(u"interface.output", data)


    def _mdp_reply_butler_scripts(self, message):
        """ Send the raw content for the brain parts over the MQ
        """

        # TODO : handle choice of the client in the req message

        # load not understood queries data
        self.read_not_understood_file()

        msg = MQMessage()
        msg.set_action('butler.scripts.result')
        msg.add_data(u"learn", self.learn_content)
        msg.add_data(u"not_understood", self.not_understood_content)
        for client_id in self.brain_content:
            msg.add_data(client_id, self.brain_content[client_id])
        self.reply(msg.get())


    def _mdp_reply_butler_reload(self, message):
        """ Reload the brain 
        """
        msg = MQMessage()
        msg.set_action('butler.reload.result')
        try:
            self.reload()
            msg.add_data(u"status", True)
            msg.add_data(u"reason", "")
        except:
            msg.add_data(u"status", False)
            msg.add_data(u"reason", "Error while reloading brain parts : {0}".format(traceback.format_exc()))
        self.reply(msg.get())


    def _mdp_reply_butler_history(self, message):
        """ Butler history
        """
        msg = MQMessage()
        msg.set_action('butler.history.result')
        msg.add_data(u"history", self.history)
        self.reply(msg.get())


    def _mdp_reply_butler_features(self, message):
        """ Butler features
        """
        msg = MQMessage()
        msg.set_action('butler.features.result')
        msg.add_data(u"features", self.butler_features)
        self.reply(msg.get())


    def reload(self):
        self.load_all_brain()


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
            and also plugin_* because some plugins may need dedicated brain parts :
            - weather forecast
            - anything less generic than a datatype basic usage
        """
        try:
            list = []
            # first load the packages parts
            dir_list = os.listdir(self.get_packages_directory())

            # first, make sure the brain_base package is loaded the first!!
            if BRAIN_BASE in dir_list:
                dir_list.remove(BRAIN_BASE)
                dir_list = [BRAIN_BASE] + dir_list

            for a_file in dir_list:
                try:
                    pkg_type, name = a_file.split("_")
                except ValueError:
                    # not a foo_bar file : skip it
                    continue
                #if a_file[0:len(BRAIN_PKG_TYPE)] == BRAIN_PKG_TYPE:
                if pkg_type in BRAIN_PKG_TYPES:
                    client_id = "{0}-{1}.{2}".format(pkg_type, a_file.split("_")[1], self.get_sanitized_hostname())
                    self.brain_content[client_id] = {}
                    rs_dir = os.path.join(self.get_packages_directory(), a_file, RIVESCRIPT_DIR)
                    if os.path.isdir(rs_dir):
                        self.log.info(u"Brain part found : {0}".format(a_file))
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

            # and finally, load the learning file
            # this file is generated over the time when the domogik.butler.brain  learn() function is called
            learn_file = LEARN_FILE
            if os.path.isfile(learn_file):
                self.log.info(u"Learn file found : {0}".format(learn_file))

                # add the brain part to rivescript
                self.brain.load_file(learn_file)
                try:
                    import codecs
                    file = codecs.open(learn_file, 'r', 'utf-8')
                    file_content = file.read()
                    file_header = "// File : {0}".format(learn_file)
                    self.learn_content = u"{0}\n\n{1}".format(file_header, file_content)
                except:
                    self.learn_content = u"Error while reading file '{0}'. Error is : {1}".format(learn_file, traceback.format_exc())
                    self.log.error(self.learn_content)
            else:
                self.learn_content = u""
                self.log.info(u"Learn file NOT found : {0}. This is not an error. You just have learn nothing to your butler ;)".format(learn_file))
            
                              
            # to finish, find all the tagged features
            # and all the tagged suggestions
            self.get_brain_features_and_suggestions()

        except:
            msg = "Error accessing packages directory : {0}. You should create it".format(str(traceback.format_exc()))
            self.log.error(msg)

    def get_brain_features_and_suggestions(self):
        """ Extract brain features and suggestions  from the rivescript files :
            // ##feature## a feature
            + feature trigger
            - feature response

            /* ##suggest##
            ? ...
            @ ...
            */
        """
        self.butler_features = []
        self.butler_suggestions = []
        try:
            self.log.info(u"Extract tagged features (##feature##) and suggestions (##suggest##) from the rivescript files")
            for client in self.brain_content:
                for lang in self.brain_content[client]:
                    for fic in self.brain_content[client][lang]:
                        the_suggests = re.findall(SUGGEST_REGEXP, self.brain_content[client][lang][fic])
                        if the_suggests != []:
                            self.butler_suggestions.extend(the_suggests)
                        for line in self.brain_content[client][lang][fic].split("\n"):
                            if re.search(FEATURE_TAG, line):
                                self.butler_features.append(line.split(FEATURE_TAG)[1])
            self.log.info(u"{0} feature(s) found".format(len(self.butler_features)))
            self.log.info(u"{0} suggestion(s) found".format(len(self.butler_suggestions)))

            # store in the Rivescript object the features and suggestions to be able to grab them from the core brain package
            self.brain.the_features = '.\n'.join(self.butler_features)
            self.brain.the_suggestions = self.butler_suggestions
        except:
            self.log.error(u"Error while extracting the features : {0}".format(traceback.format_exc()))
                 


    def process(self, query):
        """ Process the input query by calling rivescript brain
            @param query : the text query
        """
        reply = ""
        try:
            self.log.debug(u"Before transforming query : {0}".format(query))
            self.brain.raw_query = query

            query = clean_input(query)

            self.log.debug(u"After transforming query : {0}".format(query))
            self.brain.query = query

            # process the query
            self.log.debug(u"Before calling Rivescript brain for processing : {0} (type={1})".format(query, type(query)))
            reply = self.brain.reply(self.user_name, query)
            self.log.debug(u"Processing finished. The reply is : {0}".format(reply))
            return reply
        except:
            self.log.error(u"Error while processing query '{0}'. Error is : {1}".format(query, traceback.format_exc()))
            return "Error"


    def shutdown(self):
        """ Shutdown the butler
        """
        pass

    def add_to_history(self, msgid, data):
        self.history.append({"msgid" : msgid, "context" : data})

    def on_message(self, msgid, content):
        """ When a message is received from the MQ (pub/sub)
        """
        if msgid == "device.update":
            self.reload_devices()
        elif msgid == "interface.input":
            # TODO :
            # merge with the on_mdp_reply_butler_disscuss() function

            self.log.info(u"Received message : {0}".format(content))

            ### Get response from the brain
            # TODO : do it in a thread and if this last too long, do :
            # 3s : reply "humm..."
            # 10s : reply "I am checking..."
            # 20s : reply "It takes already 20s for processing, I cancel the request" and kill the thread
            #reply = self.brain.reply(self.user_name, content['text'])

            self.add_to_history(u"interface.input", content)
            reply = self.process(content['text'])

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

            # fill empty data
            for elt in ['identity', 'media', 'location', 'sex', 'mood', 'reply_to']:
                if elt not in content:
                    content[elt] = None

            # publish over MQ
            data =              {"media" : content['media'],
                                 "location" : content['location'],
                                 "sex" : self.butler_sex,
                                 "mood" : self.butler_mood,
                                 "is_reply" : True,
                                 "reply_to" : content['source'],
                                 "identity" : self.butler_name,
                                 "lang" : self.lang,
                                 "text" : reply}
            self.log.info(u"Send response over MQ : {0}".format(data))
            self.pub.send_event('interface.output',
                                data)
            self.add_to_history(u"interface.output", data)


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
            print(u"{0} > {1}".format(ucode(self.butler_name), ucode(reply)))

            # let Nestor speak
            #tts = u"espeak -p 40 -s 140 -v mb/mb-fr1 \"{0}\" | mbrola /usr/share/mbrola/fr1/fr1 - -.au | aplay".format(reply)
            #tts = u"espeak -p 40 -s 140 -v mb/mb-fr1 \"{0}\" | mbrola /usr/share/mbrola/fr1 - -.au | aplay".format(reply)
            #subp = Popen(tts, shell=True)
            #pid = subp.pid
            #subp.communicate()

    def read_not_understood_file(self):
        """ Get the content of the non understood queries file
        """
        if os.path.isfile(STAR_FILE):
            self.log.info(u"Not understood queries file found : {0}".format(STAR_FILE))

            try:
                import codecs
                file = codecs.open(STAR_FILE, 'r', 'utf-8')
                file_content = file.read()
                file_header = "// File : {0}".format(STAR_FILE)
                self.not_understood_content = u"{0}\n\n{1}".format(file_header, file_content)
            except:
                self.not_understood_content = u"Error while reading file '{0}'. Error is : {1}".format(STAR_FILE, traceback.format_exc())
                self.log.error(self.not_understood_content)
        else:
            self.not_understood_content = u""
            self.log.info(u"Not understood queries file NOT found : {0}. This is not an error. Your butler is just awesome (or unused) ;)".format(STAR_FILE))

if __name__ == "__main__":
    Butler()
