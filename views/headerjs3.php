	
    <script src="<?=$this->config->item('JS_DIR')?>prototype.js" language="JavaScript" ></script>
	<script src="<?=$this->config->item('JS_DIR')?>reflection.js" type="text/javascript" ></script>
	<script src="<?=$this->config->item('JS_DIR')?>updatemusic.js" type="text/javascript" ></script>
    <script type="text/javascript" src="<?=$this->config->item('JS_DIR')?>progress/jsProgressBarHandler.js"></script>
  	<script type="text/javascript" charset="utf-8">

	/*
	 * Chargement de la page
	 */
	(function() {
      Event.observe(document, 'dom:loaded', function() {
        new PeriodicalExecuter(updateMusic, <?=$this->config->item('AUDIO_REFRESH')?>);
        updateMusic();
	  })
    })()
  </script>
</head>
