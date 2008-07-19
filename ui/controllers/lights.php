<?php
/*
	$LastChangedBy: mschneider $
	$LastChangedDate: 2008-07-19 18:37:38 +0200 (sam. 19 juil. 2008) $
	$LastChangedRevision: 74 $
*/

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
	function getJSONState($place) {
		//Start with getting all items in the place
		$elements = $this->items->get_items($this->items->get_name_from_id($place));
		//Then get the state of the items
		return $this->items->getState($elements);

	}

    /*
     * Get State of all items from a room
     */
	function room($id) {
		$r = $this->getJSONState($id);
		$j = json_encode($r);
		$this->load->view('json', array("data" => $j));
	}

	/*
	 * Switch on an item
	 * The script *DOESN'T* update the database
	 * It must be done by the controller triggering the action
	 */
     //TODO : Call a function to send xPL message
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
     //TODO : Call a function to send xPL message
	function off($item) {
		$r = array("root" => array());
		$r["root"]["item"] = array();
		$r["root"]["item"]["name"] = $item;
		$r["root"]["item"]["value"] = 0;
		$r["root"]["item"]["description"] = $this->items->get_desc_from_name($item);
		$j = json_encode($r);
		$this->load->view('json', array("data" => $j));
	}

    //TODO : Deprecated ?
	function chambre()
	{
		$r = $this->getJSONState("chambre");
		$j = json_encode($r);
		$this->load->view('json', array("data" => $j));
	}
}
?>
