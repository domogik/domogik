<?php
/*
Copyright 2008 Domogik project

This file is part of Domogik.
Domogik is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Domogik is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Domogik.  If not, see <http://www.gnu.org/licenses/>.

Author: Maxence Dunnewind <maxence@dunnewind.net>

$LastChangedBy: mschneider $
$LastChangedDate: 2008-07-23 21:42:29 +0200 (mer. 23 juil. 2008) $
$LastChangedRevision: 100 $
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
