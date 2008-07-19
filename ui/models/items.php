<?php
/*
	$Author$
	$LastChangedBy$
	$LastChangedDate$
	$LastChangedRevision$
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
