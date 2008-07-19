<?php
/*
	$LastChangedBy: mschneider $
	$LastChangedDate: 2008-07-19 18:37:38 +0200 (sam. 19 juil. 2008) $
	$LastChangedRevision: 74 $
*/

class Application extends Controller {

    function Application()
    {
        parent::Controller();
    }

    function makeMenu()
    {
        $this->load->model("room");
        $pieces = $this->room->getRooms();
    }

}
?>
