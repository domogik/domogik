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
 * Class for information relative to the temperature
 */
class Temperature extends Model 
{
    function Model()
    {
        parent::Model();
        $this->load->model('items');
    }

    /**
     * Gets the temperatures values of a room
     * @param roomId : Id of the room
     * @return : values in JSON format
     */
    function update($roomId) 
    {
        $nom = $this->items->get_name_from_id($roomId);
        $releves = array();
        $this->db->select('date, thermometer, temperature');
        $date= getdate();
        $d = strftime("%Y-%m-%d %H:%M:%S",$date[0]-86400);
        $this->db->where("date >", $d);
        $this->db->where("name", $nom);
        $q = $this->db->get("V_STATEMENTS_ROOMS");
        //,array("date > " => $d,"nom" => $this->items->get_name_from_id($roomId))); 
        $i = 0;
         foreach ($q->result() as $row)
         {
//             if (array_key_exists($row->thermometre, $releves))
  //           {
                $releves[$row->thermometer][$i]= array(strtotime($row->date),$row->temperature);
    /*         }
             else
             {
                $releves[$i] = array(strtotime($row->date),$row->temperature);
             }*/
        $i++;
         }
        $series = array();
            $data = array("data" => json_encode(array(
                "series" => array($releves[$row->thermometer]),
                "options" => array(
                        "xaxis" => array(
                            "noTicks"=> 0, 
                            "lines" => array(
                                "show"=>'true'
                            )
                        ),
                        "yaxis" => array(
                            "min"=> 10,
                            "max" => 40,
                            "noTicks" => 3
                        ),
                        "points" => array(
                            "show" => false
                        ),
                        "lines" => array(
                            "fill" => true 
                        ),
                        "mouse" =>array(
                            "track" => true,
                            "position" => "se",
                            "trackFormatter" => "defaultTrackFormatter",
                            "margin" => 3,
                            "color" => "#FF0000",
                            "trackDecimals" => 1,
                            "sensibility" => 2,
                            "radius" => 3
                        )
                )
            )));
        $this->load->view("json",$data);
    }
}
