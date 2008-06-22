<?php
class Manager extends Model {

    function Manager()
    {
        parent::Model();
    }

    /**
     * Returns the list of the rooms
     * @return : an array array[id] = 'name' with all the rooms
     */
     public function getPieces()
     {
         $query = $this->db->get("salles");
         $res = array();
         foreach ($query->result() as $row)
         {
             $res[$row->id] = $row->nom;
         }
         return $res;
     }

     /**
      * @param ipdiece : Id of the room
      * @return : an array with the capacities of a room
      */
      public function getCapacites($idpiece)
      {
          $query = $this->db->get_where('capacites',array('id_piece' => $idpiece));
          $res = array();
          foreach($query->result() as $row)
          {
              $res[] = $row->capacite;
          }
          return $res;
      }

}
?>
