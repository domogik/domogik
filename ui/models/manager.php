<?php
/*
	$LastChangedBy: mschneider $
	$LastChangedDate: 2008-07-19 18:48:04 +0200 (sam. 19 juil. 2008) $
	$LastChangedRevision: 75 $
*/
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
             $res[$row->id] = $row->name;
         }
         return $res;
     }

     /**
      * @param roomId : Id of the room
      * @return : an array with the capacities of a room
      */
      public function getCapacites($roomId)
      {
          $query = $this->db->get_where('CAPACITIES',array('id_room' => $roomId));
          $res = array();
          foreach($query->result() as $row)
          {
              $res[] = $row->capacity;
          }
          return $res;
      }

}
?>
