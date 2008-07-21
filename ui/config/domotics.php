<?php
/*
	$LastChangedBy: mschneider $
	$LastChangedDate: 2008-07-21 11:55:28 +0200 (lun. 21 juil. 2008) $
	$LastChangedRevision: 95 $
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
