<?php
class Lights extends Controller {

	function Lights()
	{
		parent::Controller();	
        $this->load->model('items');
	}
	
	function index()
	{
		$this->load->view('home');
	}
	
	/*
	 * Renvoie un tableau de tableaux contenant des paires avec le nom et la valeur
	 * Ex :
	 * {"root" : 
	 * 			{ "item1" : 
	 * 					{ 	"name" : "A1",
	 * 						"description" : "Lampe chambre",
	 * 						"value" : 0
	 * 					},
	 * 			{ "item2" : 
	 * 					{ 	"name" : "A2",
	 * 						"description" : "Radio Cuisine",
	 * 						"value" : 1
	 * 					}
	 * 			}
	 * }
	 */
	function getJSONState($lieu) {
		//On commence par récupérer tous les éléments du lieu
		$elements = $this->items->get_items($this->items->get_name_from_id($lieu));
		//Ensuite on récupère l'état des éléments
		return $this->items->getState($elements);
		
	}
	
	function piece($id) {
		$r = $this->getJSONState($id);
		$j = json_encode($r);
		$this->load->view('json', array("data" => $j));
	}
	
	/*
	 * Allume un item
	 * La mise à jour de la base n'est *PAS* effectué par le script
	 * Elle devra être faite par le controleur effectuant l'opération
	 */
	function on($item) {
		$r = array("root" => array());
		$r["root"]["item"] = array();
		$r["root"]["item"]["name"] = $item;
		$r["root"]["item"]["value"] = 1;
		$r["root"]["item"]["description"] = $this->items->get_desc_from_name($item);
		$j = json_encode($r);
		$this->load->view('json', array("data" => $j));
	}
	
	/*
	 * Eteint un item
	 * La mise à jour de la base n'est *PAS* effectué par le script
	 * Elle devra être faite par le controleur effectuant l'opération
	 */
	function off($item) {
		$r = array("root" => array());
		$r["root"]["item"] = array();
		$r["root"]["item"]["name"] = $item;
		$r["root"]["item"]["value"] = 0;
		$r["root"]["item"]["description"] = $this->items->get_desc_from_name($item);
		$j = json_encode($r);
		$this->load->view('json', array("data" => $j));
	}
	
	function chambre()
	{
		$r = $this->getJSONState("chambre");
		$j = json_encode($r);
		$this->load->view('json', array("data" => $j));
	}
}
?>
