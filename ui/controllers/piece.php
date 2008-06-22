<?php
/**
 * This class is the central point of the application
 * It supplies all the functions relative to the structure 
 * of a page for a room (detection of capacities...)
 */
class Piece extends Controller {

	function Piece()
	{
		parent::Controller();
        $this->load->model('items');
        $this->load->model('manager');
	}

    /**
     * Index function
     * Calls lookup for the 1st room
     */
     function index()
     {
         $this->lookup("1");
     }
    
    /**
     * Default function
	 * Gets the list of capacities of the given room and loads the first capacity
     * @param idpiece : Id of the room
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
	 * Generic call for views loading of a room (for lights and power points)
     * @param data : array of parameters to supply to the views
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
     * Generic call for temperature
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
     * Generic call for music
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
     * Extenal call for electricity
	 * Loads the data for the given room and calls __piece__ to change the views
     * @param idpiece : Id of the room
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
	  * Returns the view displaying information about the music played in the room
      * @param idpiece : Id of the room
      */
    function musique($idpiece)
    {
        $data["piece"] = $idpiece;
        $data["title"] = $this->items->get_name_from_id($idpiece);
        $data["name_piece"] = $this->items->get_name_from_id($idpiece);
        
        $this->__musique__($data);
    }
}
