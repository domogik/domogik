<?php
/**
 * Classe gérant les informations relatives à la musique
 */
class Musique extends Model
{
    function Musique()
    {
        parent::Model();
        $this->load->model('items');
    }

    /**
     * Récupère les informations relative à la musique de la pièce concernée
     * @param roomId : ID de la pièce
     * @return : Informations sur le lecteur de la piece format JSON
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
     * Appel externe pour déclencher la lecture
     * @param roomId : ID de la piece dans laquelle déclencher la lecture
     */
    function playMusic($roomId)
    {
    }

    /**
     * Appel externe pour déclencher la lecture
     * @param roomId : ID de la piece dans laquelle déclencher la pause 
     */
    function pauseMusic($roomId)
    {
    }

    /**
     * Appel externe pour déclencher la lecture
     * @param roomId : ID de la piece dans laquelle arrêter la lecture
     */
    function stopMusic($roomId)
    {
    }
}
