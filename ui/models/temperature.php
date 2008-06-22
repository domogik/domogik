<?php
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
        $this->db->select('date, thermometre, temperature');
        $date= getdate();
        $d = strftime("%Y-%m-%d %H:%M:%S",$date[0]-86400);
        $this->db->where("date >", $d);
        $this->db->where("nom", $nom);
        $q = $this->db->get("VRelevesSalles");
        //,array("date > " => $d,"nom" => $this->items->get_name_from_id($roomId))); 
        $i = 0;
         foreach ($q->result() as $row)
         {
//             if (array_key_exists($row->thermometre, $releves))
  //           {
                $releves[$row->thermometre][$i]= array(strtotime($row->date),$row->temperature);
    /*         }
             else
             {
                $releves[$i] = array(strtotime($row->date),$row->temperature);
             }*/
        $i++;
         }
        $series = array();
            $data = array("data" => json_encode(array(
                "series" => array($releves[$row->thermometre]),
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
