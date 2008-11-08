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
# $LastChangedDate: 2008-11-08 09:44:24 +0100 (sam. 08 nov. 2008) $
# $LastChangedRevision: 188 $

Note
====
To learn using Django, there is an excellent tutorial here :
http://docs.djangoproject.com/en/dev/intro/tutorial01/#intro-tutorial01

Requirements
============
* Make sure you have a database installed (mySql, PostgreSQL, ...)
* Make sure you have Python installed
* Make sure you have Python MySql package installed (or the package relative to your DB)
	For Debian / Ubuntu :
		* mySql 		: python-mysqldb
		* PostgreSQL 	: python-pgsql python-psycopg

Installing Django
=================

* Download the latest version of django and uncompress the archive :
	Go to http://www.djangoproject.com/download/
* Install it by running :
	python setup.py install

Run Django development embedded-server
======================================
python manage.py runserver [port] # Default is 8000

Install the application
=======================

* Create a database named 'domogik'

* Create settings_local.py and override values defined in settings.py if they
don't match your local configuration (DB type, DB user, DB password, TEMPLATE_DIRS...)

* Edit urls.py (in the 'domogik' directory)
	# TODO : this should be changed : find a way to put this in settings_local.py (see above)
	Go to django.views.static.serve and set path to yours

* Create tables for the app
	# Go to the 'domogik' directory
	python manage.py syncdb
	# Enter a username / password (this is for the admin part of Django [not the Domogik one])

* Initialize the app
	* Point your browser to : http://localhost:8000/domogik/admin
	* Click on the button to load sample data
	* Click to the link to go back to the admin main page
	* Click to the ling to go to the main page of the app
	* Enjoy !

* Manage data
	* You can easily add / update / remove data in the app, using the Django's
	admin interface.
	* Point your browser to : http://127.0.0.1:8000/admin
	* Username / password is the one you entered when you run 'python manage.py syncdb'
