<?php
/*
	$LastChangedBy: mschneider $
	$LastChangedDate: 2008-07-19 18:55:17 +0200 (sam. 19 juil. 2008) $
	$LastChangedRevision: 76 $
*/
?>

<div id="music">
    <div id="container">
        <h3 id="musictitle"><?=$title?></h3>
        <p id="duree"><p>
        <span class="progressBar" id="progress"></span>
        <br />
        <div id="musicimg">
            <img id="play" src="<?=$this->config->item('IMAGES_DIR')?>play.png"/>
            <img id="pause" src="<?=$this->config->item('IMAGES_DIR')?>pause.png"/>
            <img id="stop" src="<?=$this->config->item('IMAGES_DIR')?>stop.png"/>
        </div>
    </div>
</div>
