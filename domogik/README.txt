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
# $LastChangedDate: 2008-10-04 18:34:00 +0200 (sam. 04 oct. 2008) $
# $LastChangedRevision: 118 $

Requirements
============
* Make sure you have Python installed
* Make sure you have Python MySql package installed

Installing Django
=================

* Download the latest version of django and uncompress the archive
* Install it by running : sudo python setup.py install

Run Django development embedded-server
======================================
python manage.py runserver [port] # Default is 8000

Install the database
====================

* Edit settings.py and adapt DB parameters to your environment

* Create initial tables for the framework
	python manage.py syncdb
