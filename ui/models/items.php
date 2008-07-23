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
class Items extends Model {
    
    function Items() 
    {
        parent::Model();
    }

	function get_name_from_id($id) {
		$query = $this->db->get_where("ROOMS",array("id" => $id));
		$row = $query->first_row();
		return $row->name;
	}

	function get_desc_from_name($name) {
		$query = $this->db->get_where("ITEMS",array("name" => $name));
		$row = $query->first_row();
		return $row->description;
	}

	/*
     * Returns all the items of a room
	 * Gets the list of the entries corresponding to the place
     * using the 'localisation' table
	 */
	function get_items($place) {
		$query = $this->db->get_where("V_ITEMS_ROOMS",array("nameR" => $place));
		$list = array();
		foreach ($query->result() as $row)
	    {
		    $list[count($list)] = $row->nomE;
	    }
	    return $list;
	}

	/*
	 * Returns the states of a list of items
	 */
	function getState($items) {
		$result = array("root" => array());
		$nb = 0;
		foreach ($items as $i) {
			$query = $this->db->get_where("V_STATES_ITEMS",array("name" => $i));
			foreach($query->result() as $row) {
				$result["root"]["item".$nb]["name"] = $row->nom;
				$result["root"]["item".$nb]["value"] = intval($row->etat);
				$result["root"]["item".$nb]["description"] = $row->description;
				$nb++;
			}
		}
		return $result;
	}

}
