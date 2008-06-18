<?php
/**
 * Cette classe est le point central de l'application.
 * Elle fournit l'ensemble des fonctions relative à la structuration 
 * d'une page pour une piece (détection capacités, etc ...)
 */
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
        $this->load->view('headermenu',$data);
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
        $this->load->view('headermenu',$data);
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
        $this->load->view('headermenu',$data);
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
    function musique($idpiece)
    {
        $data["piece"] = $idpiece;
        $data["title"] = $this->items->get_name_from_id($idpiece);
        $data["name_piece"] = $this->items->get_name_from_id($idpiece);
        
        $this->__musique__($data);
    }
}
