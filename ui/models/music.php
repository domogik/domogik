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

/**
 * Class for information relative to the music
 */
class Musique extends Model
{
    function Musique()
    {
        parent::Model();
        $this->load->model('items');
    }

    /**
	 * Gets the information about the music of a given room
     * @param roomId : Id of the room
     * @return : Information about the player of the room (JSON format)
     */
    function update($roomId)
    {
        $data["room"] = $roomId;
        $data["title"] = $this->items->get_name_from_id($roomId);
        $data["room_name"] = $this->items->get_name_from_id($roomId);
        
        $q = $this->db->get_where("MUSIC",array("id_room"=>$roomId));
        $r = $q->first_row();
        list($hour, $minutes, $seconds) = explode(":", $r->temps);
        list($ahour, $aminutes, $aseconds) = explode(":", $r->temps_actuel);
        $d1 = $hour * 3600 + $minutes * 60 + $seconds;
        $d2 = $ahour * 3600 + $aminutes * 60 + $aseconds;
        $d = ((int) ($d2 / ($d1 / 100)));
        $root = array();
        $root["time_percent"] = $d;
        $root["time_min"] = $r->time;
        $root["title"] = $r->title;
        $root["period"] = $r->current_time;
        $root["state"] = $r->state;

        $this->load->view("json",array("data"  => json_encode(array("root" => $root))));
    }

    /**
	 * External call to start playing
     * @param roomId : Id of the room
     */
    function playMusic($roomId)
    {
    }

    /**
     * External call for Pause function
     * @param roomId : Id of the room
     */
    function pauseMusic($roomId)
    {
    }

    /**
     * External call for stop playing music
     * @param roomId : Id of the room
     */
    function stopMusic($roomId)
    {
    }
}
