<?php
/*
	$LastChangedBy: mschneider $
	$LastChangedDate: 2008-07-19 18:37:38 +0200 (sam. 19 juil. 2008) $
	$LastChangedRevision: 74 $
*/

/**
 * Class used to call update functions of the corresponding model
 */
class Update extends Controller
{
    public function Update()
    {
        parent::Controller();
    }

	// TODO : rename this function
    function musique($roomId)
    {
        $this->load->model('music');
        $this->music->update($roomId);
    }
}

