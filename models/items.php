<?php
class Items extends Model {
    
    function Items() 
    {
        parent::Model();
    }

	/*
	 * Retourne le nom de la piece en fonction de l'id
	 */
	function get_name_from_id($id) {
		$query = $this->db->get_where("salles",array("id" => $id));
		$row = $query->first_row();
		return $row->nom;
	}

	/*
	 * Retourne la description de l'item en fonction du nom
	 */
	function get_desc_from_name($name) {
		$query = $this->db->get_where("elements",array("nom" => $name));
		$row = $query->first_row();
		return $row->description;
	}

	/*
	 * Renvoie la liste des éléments d'une pièce
	 * Va chercher la liste des entrées correspondant au lieu
	 * dans la table localisation
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
	 * Récupère les valeurs des éléments du tableau $items
	 * et recherche leur état dans la base
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
