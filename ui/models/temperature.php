<?php
/**
 * Classe permettant de gérer les appels relatifs à la température
 */
class Temperature extends Model 
{
    function Model()
    {
        parent::Model();
        $this->load->model('items');
    }

    /**
     * Récupération des relevés des thermomètres de la pièce
     * @param idpiece : ID de la piece
     * @return données des relevés au format JSON
     */
    function update($idpiece) 
    {
        $nom = $this->items->get_name_from_id($idpiece);
        $releves = array();
        $this->db->select('date, thermometre, temperature');
        $date= getdate();
        $d = strftime("%Y-%m-%d %H:%M:%S",$date[0]-86400);
        $this->db->where("date >", $d);
        $this->db->where("nom", $nom);
        $q = $this->db->get("VRelevesSalles");
        //,array("date > " => $d,"nom" => $this->items->get_name_from_id($idpiece))); 
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
