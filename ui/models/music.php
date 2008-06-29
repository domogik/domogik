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
     * @param idpiece : ID de la pièce
     * @return : Informations sur le lecteur de la piece format JSON
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
     * Appel externe pour déclencher la lecture
     * @param idpiece : ID de la piece dans laquelle déclencher la lecture
     */
    function playMusic($idpiece)
    {
    }

    /**
     * Appel externe pour déclencher la lecture
     * @param idpiece : ID de la piece dans laquelle déclencher la pause 
     */
    function pauseMusic($idpiece)
    {
    }

    /**
     * Appel externe pour déclencher la lecture
     * @param idpiece : ID de la piece dans laquelle arrêter la lecture
     */
    function stopMusic($idpiece)
    {
    }
}
