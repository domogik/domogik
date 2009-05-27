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

# Author : Marc Schneider <marc@domogik.org>

# $LastChangedBy: maxence $
# $LastChangedDate: 2009-03-21 14:33:23 +0100 (sam. 21 mars 2009) $
# $LastChangedRevision: 417 $

See the web site on http://www.domogik.org to get the latest documentation.

***********************************************************
*	Temporarily doc
*	This won't be necessary as soon as we have an installer
***********************************************************

* Install all required components (see http://www.domogik.org)
* You need to add the domogik directory to python path. One way 
  to do that is to create a file /usr/lib/python2.5/site-packages/domogik.pth
  which will contains the absolute path to the domogik root directory. If you're using
  python2.6, the file should be /usr/lib/python2.6/dist-packages/domogik.pth.

X10
***

* Install heyu (for x10 technology)
  * Plug in your CM11 device. Check /var/log/messages to see to which tty it was attached.
    This will be asked when running "make install"
  * ./Configure
  * make
  * make install (as root)

  * make sure it is running properly, running manual commands. Then stop heyu.

* Go to the 'config' directory and run :
	python generate_config.py
* Go to the 'xPL' directory and start xPL hub :
	./xPL_Hub -interface lo
	# or if you want to have more output
	./xPL_Hub -nodaemon -xpldebug -interface lo

* Go to the 'xPL' directory and run x10
	python x10_main.py

* Point your browser to your domogik installation
* Click on the "config" link and set up your devices
	(to have examples, you can first go to the admin section and load sample data)
* You should be able to send x10 commands!
