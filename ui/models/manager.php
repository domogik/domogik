<?php
class Manager extends Model {

    function Manager()
    {
        parent::Model();
    }

    /**
     * Retourne la liste des pièces 
     * @return un tableau tab[id] = 'nom' avec toutes les pièces
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
      * Retourne la liste des capacités d'une piece
      * @param ipdiece : ID de la piece
      * @return un tableau contenant les capacités de la piece
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
