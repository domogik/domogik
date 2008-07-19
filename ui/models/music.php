<?php
/*
	$LastChangedBy: mschneider $
	$LastChangedDate: 2008-07-19 18:48:04 +0200 (sam. 19 juil. 2008) $
	$LastChangedRevision: 75 $
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
