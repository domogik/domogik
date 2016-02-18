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

from domogik.scenario.actions.abstract import AbstractAction
import subprocess


class ShellAction(AbstractAction):
    """ Execute a shell script
    """

    def __init__(self, log=None, params=None):
        AbstractAction.__init__(self, log)
        self.set_description("Execute a shell command.")

    def do_action(self, local_vars):
        shell_command = self._params['shell_command']
        # local variables
        shell_command = self.process_local_vars(local_vars, shell_command)

        self._log.info("Execute the shell script {0}".format(shell_command))
        cmd = subprocess.Popen(shell_command.split(),
                                stdout = subprocess.PIPE)
        stdout = cmd.communicate()[0]
        self._log.debug("Output for shell command {0} : \n{1}".format(shell_command, stdout))

    def get_expected_entries(self):
        return {'shell_command': {'type': 'string',
                            'description': 'Shell command',
                            'default': 'echo "Hello world"'}
               }
