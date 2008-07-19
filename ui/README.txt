# $LastChangedBy: mschneider $
# $LastChangedDate: 2008-07-19 16:14:26 +0200 (sam. 19 juil. 2008) $
# $LastChangedRevision: 66 $

=====================================
=== INSTALLATION FROM SVN SOURCES ===
=====================================

The interface is coded in php5 with the CodeIgniter framework.

* Requirements
- php5, mysql

* Installation

1) CodeIgniter

* Download CodeIgniter and uncompress it where your web sites are stored. Rename it 'domogik'.
http://codeigniter.com/

2) Download Domogik project and copy directories

Download the latest (SVN) version at https://labs.libre-entreprise.org/snapshots.php?group_id=135
and : 

a) Copy the directories

* ui/config
* ui/controllers
* ui/views
* ui/models

into the system/application directory of the web site you created above (see 1) ).

b) Copy the ui/include directory at the root of the web site directory.


4) Database

* In the web site directory edit the 'system/application/config/autoload.php' file and add the 'database' library
	$autoload['libraries'] = array('database');

* In mysql create a database 'domogik' (use UTF-8 mode).
* In the web site directory go to the file system/application/config/database.php and adapt the settings for the database connection.

	$db['default']['username'] = "username";
	$db['default']['password'] = "password";
	$db['default']['database'] = "domogik";

* Execute in this database the ui/base.sql script.

5) Setup

In the web site directory edit 'system/application/config/routes.php' and put 'room' in 'default_controller'.

* Working :

With the interface you can see the rooms which are displayed in the left menu. These rooms are defined in the 'rooms' table.
Each room contains some capacities (also called functionnalities). Up to now the capacities are : temperature, light, music.
The list of capacities for each room are defined in the 'capacites' table. The capacities of a room are displayed on the right
side of the interface.

Details of the capacities :

Light :

The function of the 'light' capacity is to get the status of electrical items in a room (light, power points).
The list of items bound to a room are defined in the 'items' table.

The relationship between items and rooms are defined in the 'r_items_rooms' table.
The status of an item is defined in the 'states' table.
The status of an item is regularly read by the interface (default all 3 seconds) and red or green light is displayed.

Temperature :

The 't_statements' table contains the thermometer id, date / time of the reading and its value.
Each room can have several thermometers. The relationships are defined in the 'r_thermometer_rooms' table.
In the 'r_thermometer_name' table you have the name and a description of each thermometer.

The 'temperature' page of the interface displays all the statements of the last 24 hours in the current room and generates a graph (with the jsgraph library).
It is updated each 5 minutes (by default).

Music :

With the 'music' page you eventually can control an audio player. This page uses the 'music' table to get information about the song played, that is to
say :
- Title
- Global time
- Current time
- Play status (play, pause, stop).

The data is reloaded each 2 seconds. The Play, Pause and Stop buttons are enabled / disabled according to the play status.

Maxence (maxence@dunnewind.net)

