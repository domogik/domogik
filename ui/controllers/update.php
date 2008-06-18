<?php
/**
 * Classe permettant juste d'appeler les bonnes fonctions d'update dans le modèle correspondant
 */
class Update extends Controller
{
    public function Update()
    {
        parent::Controller();
    }

    function musique($idpiece)
    {
        $this->load->model('musique');
        $this->musique->update($idpiece);
    }
}

