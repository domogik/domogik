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

# $LastChangedBy: mschneider $
# $LastChangedDate: 2009-02-07 22:06:10 +0100 (sam. 07 févr. 2009) $
# $LastChangedRevision: 346 $

See the web site on http://www.domogik.org to get the latest documentation.

***********************************************************
*	Temporarily doc
*	This won't be necessary as soon as we have an installer
***********************************************************

* Install all required components (see http://www.domogik.org)

X10
***

* Install heyu (for x10 technology and make sure it is running properly, running
	manual commands. Then stop heyu.

* Go to the 'config' directory and run :
	python generate_config all
* Go to the 'xPL' directory and start xPL hub :
	./xPL_Hub
	# or if you want to have more output
	./xPL_Hub -nodaemon -xpldebug

* Go to the 'xPL' directory and run x10
	python x10_main.py

* Point your browser to your domogik installation
* Click on the "config" link and set up your devices
	(to have examples, you can first go to the admin section and load sample data)
* You should be able to send x10 commands!
