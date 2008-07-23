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
