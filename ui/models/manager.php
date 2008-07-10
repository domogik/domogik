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
     public function getRooms()
     {
         $query = $this->db->get("ROOMS");
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
      public function getCapacites($roomId)
      {
          $query = $this->db->get_where('CAPACITIES',array('id_room' => $roomId));
          $res = array();
          foreach($query->result() as $row)
          {
              $res[] = $row->capacite;
          }
          return $res;
      }

}
?>
