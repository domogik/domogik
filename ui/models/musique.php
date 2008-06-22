<?php
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
     * @param idpiece : Id of the room
     * @return : Information about the player of the room (JSON format)
     */
    function update($idpiece)
    {
        $data["piece"] = $idpiece;
        $data["title"] = $this->items->get_name_from_id($idpiece);
        $data["name_piece"] = $this->items->get_name_from_id($idpiece);
        
        $q = $this->db->get_where("musique",array("id_piece"=>$idpiece));
        $r = $q->first_row();
        list($hour, $minutes, $seconds) = explode(":", $r->temps);
        list($ahour, $aminutes, $aseconds) = explode(":", $r->temps_actuel);
        $d1 = $hour * 3600 + $minutes * 60 + $seconds;
        $d2 = $ahour * 3600 + $aminutes * 60 + $aseconds;
        $d = ((int) ($d2 / ($d1 / 100)));
        $root = array();
        $root["temps_percent"] = $d;
        $root["temps_min"] = $r->temps;
        $root["titre"] = $r->titre;
        $root["duree"] = $r->temps_actuel;
        $root["etat"] = $r->etat;

        $this->load->view("json",array("data"  => json_encode(array("root" => $root))));
    }

    /**
	 * External call to start playing
     * @param idpiece : Id of the room
     */
    function playMusic($idpiece)
    {
    }

    /**
     * External call for Pause
     * @param idpiece : Id of the room
     */
    function pauseMusic($idpiece)
    {
    }

    /**
     * External call for Stop
     * @param idpiece : Id of the room
     */
    function stopMusic($idpiece)
    {
    }
}
