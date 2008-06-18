<div id="music">
    <div id="container">
        <h3><?=$titre?></h3>
        <p id="duree"><?=$duree?> / <?=$temps_min?></p>
        <span class="progressBar" id="progress"><?=$temps_percent?>%</span>
        <br />
        <div id="musicimg">
            <img id="play" src="<?=$this->config->item('IMAGES_DIR')?>play.png"/>
            <img id="pause" src="<?=$this->config->item('IMAGES_DIR')?>pause.png"/>
            <img id="stop" src="<?=$this->config->item('IMAGES_DIR')?>stop.png"/>
        </div>
    </div>
</div>
