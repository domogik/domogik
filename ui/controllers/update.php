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

    function musique($roomId)
    {
        $this->load->model('musique');
        $this->musique->update($roomId);
    }
}

