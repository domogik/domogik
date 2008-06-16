<?php
class Application extends Controller {

    function Application()
    {
        parent::Controller();
    }

    function makeMenu()
    {
        $this->load->model("piece");
        $pieces = $this->piece->getPieces();
    }

}
?>
