<?php
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
