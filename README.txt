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

X10
***

* Install heyu (for x10 technology)
  * Plug in your CM11 device. Check /var/log/messages to see to which tty it was attached.
    This will be asked when running "make install"
  * ./Configure
  * make
  * make install (as root)

  * make sure it is running properly, running manual commands. Then stop heyu.

on the main directory :
    sudo python ./setup.py develop

Then to configure sample file :
	python src/domogik/bin/generate_config.py
At the moment, you can answer 'N' when prompted for database configuration.

* start xPL hub :
	src/domogik/xpl/tools/xPL_Hub -interface lo
	or if you want to have more output
	src/domogik/xpl/tools/xPL_Hub -nodaemon -xpldebug -interface lo

    python src/domogik/xpl/bin/databasemanager.py

To start x10 module :
    python src/domogik/xpl/bin/x10.py

then to start the django interface :
    cd src/domogik/ui/djangodomo
    python manage.py syncdb
    python manage.py runserver

* Point your browser to your domogik installation at http://localhost:8000/domogik
* Click on the "config" link and set up your devices
	(to have examples, you can first go to the admin section and load sample data)
* You should be able to send x10 commands!
