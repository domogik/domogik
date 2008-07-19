<?php
/*
	$LastChangedBy: mschneider $
	$LastChangedDate: 2008-07-19 18:48:04 +0200 (sam. 19 juil. 2008) $
	$LastChangedRevision: 75 $
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
"musique" => "audio",
"lumiere" => "lumiere"
);

?>
