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

/**
 * This class is the central point of the application
 * It supplies all the functions relative to the structure 
 * of a page for a room (detection of capacities...)
 */
class room extends Controller {

	function Room()
	{
		parent::Controller();
        $this->load->model('items');
        $this->load->model('manager');
	}

    /**
     * Index function
     * Calls lookup for the 1st room
     */
     //TODO call some model functions to get the first entry in database, in case of 1 doesn't exist
     function index()
     {
         $this->lookup("1");
     }
    
    /**
     * Default function
	 * Gets the list of capacities of the given room and loads the first capacity
     * @param roomId : Id of the room
     */
	function lookup($roomId)
	{
        $data = Array();
        $data["room"] = $roomId;
        $data["title"] = $this->items->get_name_from_id($roomId);
        $data["name_room"] = $this->items->get_name_from_id($roomId);
        $capa = $this->manager->getCapacites($roomId);
        if (sizeof($capa) != 0)
        {
            switch($capa[0])
            {
                case "light":
                    $this->__room__($data);
                    break;
                case "temperature":
                    $this->__temperature__($data);
                    break;
                case "music":
                    $this->__musique__($data);
                    break;
            }
        }
        else
        {
		    $this->__room__($data);
        }
	}

    /**
	 * Generic call for views loading of a room (for lights and power points)
     * @param data : array of parameters to supply to the views
     */
    private function __room__($data)
    {
        $data["menu"] = $this->manager->getRooms();
        $data["capacities"] = $this->manager->getCapacites($data["room"]);
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
        $data["menu"] = $this->manager->getRooms();
        $data["capacities"] = $this->manager->getCapacites($data["room"]);
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
	// TODO rename this function to '__music__'
    private function __music__($data)
    {
        $data["menu"] = $this->manager->getRooms();
        $data["capacities"] = $this->manager->getCapacites($data["room"]);
        $this->load->view('head',$data);
        $this->load->view('configjs');
        $this->load->view('headerjs3',$data);
        $this->load->view('headermenu',$data);
        $this->load->view('music');
        $this->load->view('footer');
    }

    /**
     * Extenal call for electricity
	 * Loads the data for the given room and calls __room__ to change the views
     * @param idroom : Id of the room
     */
    function light($roomId)
    {
        $data = Array();
        $data["room"] = $roomId;   
        $data["title"] = $this->items->get_name_from_id($roomId);
        $data["name_room"] = $this->items->get_name_from_id($roomId);
		$this->__room__($data);
	}

    function temperature($roomId)
    {
        $data["room"] = $roomId;   
        $data["title"] = $this->items->get_name_from_id($roomId);
        $data["name_room"] = $this->items->get_name_from_id($roomId);
        $this->__temperature__($data);         
    }

    /**
	  * Returns the view displaying information about the music played in the room
      * @param roomId : Id of the room
      */
    function music($roomId)
    {
        $data["room"] = $roomId;
        $data["title"] = $this->items->get_name_from_id($roomId);
        $data["name_room"] = $this->items->get_name_from_id($roomId); 
        $this->__music__($data);
    }
}
