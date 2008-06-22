<?php
/**
 * Class used to call update functions of the corresponding model
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

