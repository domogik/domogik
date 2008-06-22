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
	 * Return an array of arrays containing pairs (name, value)
	 * Ex :
	 * {"root" : 
	 * 			{ "item1" : 
	 * 					{ 	"name" : "A1",
	 * 						"description" : "Bedroom Light",
	 * 						"value" : 0
	 * 					},
	 * 			{ "item2" : 
	 * 					{ 	"name" : "A2",
	 * 						"description" : "Kitchen Radio",
	 * 						"value" : 1
	 * 					}
	 * 			}
	 * }
	 */
	function getJSONState($lieu) {
		//Start with getting all items in the place
		$elements = $this->items->get_items($this->items->get_name_from_id($lieu));
		//Then get the state of the items
		return $this->items->getState($elements);
		
	}
	
	function piece($id) {
		$r = $this->getJSONState($id);
		$j = json_encode($r);
		$this->load->view('json', array("data" => $j));
	}
	
	/*
	 * Switch on an item
	 * The script *DOESN'T* update the database
	 * It must be done by the controller triggering the action
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
	 * Switch off an item
	 * The script *DOESN'T* update the database
	 * It must be done by the controller triggering the action
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
