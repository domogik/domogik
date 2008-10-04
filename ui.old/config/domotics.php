<?php
/*
Copyright 2008 Domogik project

This file is part of Domogik.
Domogik is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Domogik is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Domogik.  If not, see <http://www.gnu.org/licenses/>.

Author: Maxence Dunnewind <maxence@dunnewind.net>

$LastChangedBy: mschneider $
$LastChangedDate: 2008-07-23 21:42:29 +0200 (mer. 23 juil. 2008) $
$LastChangedRevision: 100 $
*/

if (!defined('BASEPATH')) exit('No direct script access allowed');
$config = array();

/*******************************/
/*  Refresh times (in seconds) */
/*******************************/

//Page for lights and power points
$config['LIGHT_REFRESH'] = 3;

//Page for temperature
$config['TEMP_REFRESH'] = 300;

//Page for music
$config['AUDIO_REFRESH'] = 2;

/******************************/
/*       Capacities           */
/******************************/
/*
 * Capacities describe which functionnalities are present in each room
 * They are stored in the table 'capacities'
 * This array defines which function will be called for each capacity
 * The function must be declared in the 'Room' controller
 */
$config['CAPACITIES'] = array(
"temperature" => "temperature",
"music" => "audio",
"light" => "lumiere"
);

?>
