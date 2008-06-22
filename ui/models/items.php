<?php
class Items extends Model {
    
    function Items() 
    {
        parent::Model();
    }

	function get_name_from_id($id) {
		$query = $this->db->get_where("salles",array("id" => $id));
		$row = $query->first_row();
		return $row->nom;
	}

	function get_desc_from_name($name) {
		$query = $this->db->get_where("elements",array("nom" => $name));
		$row = $query->first_row();
		return $row->description;
	}

	/*
     * Returns all the items of a room
	 * Gets the list of the entries corresponding to the place
     * using the 'localisation' table
	 */
	function get_items($lieu) {
		$query = $this->db->get_where("vue",array("nomS" => $lieu));
		$liste = array();
		foreach ($query->result() as $row)
	    {
		    $liste[count($liste)] = $row->nomE;
	    }
	    return $liste;
	}

	/*
	 * Returns the states of a list of items
	 */
	function getState($items) {
		$result = array("root" => array());
		$nb = 0;
		foreach ($items as $i) {
			$query = $this->db->get_where("VEtatsElements",array("nom" => $i));
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
