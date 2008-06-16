<?php
class Piece extends Controller {

	function Piece()
	{
		parent::Controller();
        $this->load->model('items');
        $this->load->model('manager');
	}

    /**
     * Fonction d'index
     * Appelera lookup sur la première piece
     */
     function index()
     {
         $this->lookup("1");
     }
    
    /**
     * Fonction par defaut
     * Récupère la liste des capacités de la piece concernée et charge la premiere capacite
     * @param idpiece : l'id de la piece concernee
     */
	function lookup($idpiece)
	{
        $data = Array();
        $data["piece"] = $idpiece;
        $data["title"] = $this->items->get_name_from_id($idpiece);
        $data["name_piece"] = $this->items->get_name_from_id($idpiece);
        $capa = $this->manager->getCapacites($idpiece);
        if (sizeof($capa) != 0)
        {
            switch($capa[0])
            {
                case "lumiere":
                    $this->__piece__($data);
                    break;
                case "temperature":
                    $this->__temperature__($data);
                    break;
                case "musique":
                    $this->__musique__($data);
                    break;
            }
        }
        else
        {
		    $this->__piece__($data);
        }
	}

    /**
     * Appel générique pour le chargement des vues pour une piece (pour les lumières et les prises)
     * @param data : le tableau de paramètre à passer aux vues
     */
    private function __piece__($data)
    {
        $data["menu"] = $this->manager->getPieces();
        $data["capacites"] = $this->manager->getCapacites($data["piece"]);
        $this->load->view('head',$data);
        $this->load->view('configjs');
        $this->load->view('headerjs',$data);
        $this->load->view('body', $data);
        $this->load->view('footer');
    }

    /**
     * Appel générique pour la température
     * @param data
     **/
     private function __temperature__($data)
     {
        $data["menu"] = $this->manager->getPieces();
        $data["capacites"] = $this->manager->getCapacites($data["piece"]);
        $this->load->view('head',$data);
        $this->load->view('configjs');
        $this->load->view('headerjs2',$data);
        $this->load->view("temper");
        $this->load->view('footer');
     }

    /**
     * Appel générique pour la musique
     */
     private function __musique__($data)
     {
        $data["menu"] = $this->manager->getPieces();
        $data["capacites"] = $this->manager->getCapacites($data["piece"]);
        $this->load->view('head',$data);
        $this->load->view('configjs');
        $this->load->view('headerjs3',$data);
        $this->load->view('music');
        $this->load->view('footer');
     }

    /**
     * Appel externe pour l'electricite
     * Charge les données pour la piece concernée et appel __piece__ pour charger les vues
     * @param idpiece : Id de la pièce
     */
    function lumiere($idpiece)
    {
        $data = Array();
        $data["piece"] = $idpiece;   
        $data["title"] = $this->items->get_name_from_id($idpiece);
        $data["name_piece"] = $this->items->get_name_from_id($idpiece);
		$this->__piece__($data);
	}

    function update($idpiece) 
    {
        $nom = $this->items->get_name_from_id($idpiece);
        $releves = array();
        $this->db->select('date, thermometre, temperature');
        $date= getdate();
        $d = strftime("%Y-%m-%d %H:%M:%S",$date[0]-86400);
        $this->db->where("date >", $d);
        $this->db->where("nom", $nom);
        $q = $this->db->get("VRelevesSalles");
        //,array("date > " => $d,"nom" => $this->items->get_name_from_id($idpiece))); 
        $i = 0;
         foreach ($q->result() as $row)
         {
//             if (array_key_exists($row->thermometre, $releves))
  //           {
                $releves[$row->thermometre][$i]= array(strtotime($row->date),$row->temperature);
    /*         }
             else
             {
                $releves[$i] = array(strtotime($row->date),$row->temperature);
             }*/
        $i++;
         }
        $series = array();
            $data = array("data" => json_encode(array(
                "series" => array($releves[$row->thermometre]),
                "options" => array(
                        "xaxis" => array(
                            "noTicks"=> 0, 
                            "lines" => array(
                                "show"=>'true'
                            )
                        ),
                        "yaxis" => array(
                            "min"=> 10,
                            "max" => 40,
                            "noTicks" => 3
                        ),
                        "points" => array(
                            "show" => false
                        ),
                        "lines" => array(
                            "fill" => true 
                        ),
                        "mouse" =>array(
                            "track" => true,
                            "position" => "se",
                            "trackFormatter" => "defaultTrackFormatter",
                            "margin" => 3,
                            "color" => "#FF0000",
                            "trackDecimals" => 1,
                            "sensibility" => 2,
                            "radius" => 3
                        )
                )
            )));
        $this->load->view("json",$data);
    }

    function temperature($idpiece)
    {
        $data["piece"] = $idpiece;   
        $data["title"] = $this->items->get_name_from_id($idpiece);
        $data["name_piece"] = $this->items->get_name_from_id($idpiece);
        $this->__temperature__($data);         
    }

    /**
      * Renvoie la vue permettant d'afficher des informations 
      * sur la musique en cours dans la piece
      * @param id de la piece
      */

    function audio($idpiece)
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
        $data["temps"] = $d;
        $this->__musique__($data);
    }

    function update_audio($idpiece)
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
        $root["temps"] = $d;

        $this->load->view("json",array("data"  => json_encode(array("root" => $root))));
    }
}
