=== Information about the current version of the interface ===

* Requirements
- php5, mysql

* Installation

The interface is coded in php5 with the CodeIgniter framework.

1) CodeIgniter

* Download CodeIgniter and uncompress it where your web sites are stored. Rename it 'domogik'.

2) Directories copy
The directories :
* config/
* controllers/
* views/
* models/
must be copied into the system/application directory of CodeIgniter.

The include directory must be copied at the root of the web site you created above (with the current configuration).

The last step is to add the 'database' library in the file system/application/config/autoload.php of CodeIgniter.

3) Database

* In mysql create a database 'domogik' (use UTF-8 mode).
* Go to the file system/application/config/database.php and adapt the settings for the database connection.
* Execute in this database the base.sql script.

4) Setup

Edit config/routes.php and put 'piece' in 'default_controller'.


* Working :

With the interface you can see the rooms which are displayed in the left menu. These rooms are defined in the 'salle' table.
Each room contains some capacities (also called functionnalities). Up to now the capacities are : temperature, light, music.
The list of capacities for each room are defined in the 'capacites' table. The capacities of a room are displayed on the right
side of the interface.

Details of the capacities :

Light :

The function of the 'light' capacity is to get the status of electrical items in a room (light, power points).
The list of items bound to a room are defined in the 'element' table.

The relationship between items and rooms are defined in the 'RElementsSalles' table.
The status of an item is defined in the "etats" table.
The status of an item is regularly read by the interface (default all 3 seconds) and red or green light is displayed.

Temperature :

The 'Treleves' table contains the thermometer id, date / time of the reading and its value.
Each room can have several thermometers. The relationships are defined in the 'RThermometreSalles' table.
In the 'RThermometreNom' you have the name and a description of each thermometer.

The 'temperature' page of the interface displays all the readings of the last 24 hours in the current room and generates a graph (with the jsgraph library).
It is updated each 5 minutes (by default).

Music :

With the 'music' page you eventually can control an audio player. This page uses the 'musique' table to get information about the song played, that is to
say :
- Title
- Global time
- Current time
- Play status (play, pause, stop).

The data is reloaded each 2 seconds. The Play, Pause and Stop buttons are enabled / disabled according to the play status.

Maxence (maxence@dunnewind.net)

