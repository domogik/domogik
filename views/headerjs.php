	
    <script src="<?=$this->config->item('JS_DIR')?>prototype.js" language="JavaScript" ></script>
	<script src="<?=$this->config->item('JS_DIR')?>reflection.js" type="text/javascript" ></script>
    
	<script src="<?=$this->config->item('JS_DIR')?>updateimages.js" type="text/javascript" ></script>
  	<script type="text/javascript" charset="utf-8">

	/*
	 * Chargement de la page
	 */
	(function() {
      Event.observe(document, 'dom:loaded', function() {
	  load($('idpiece').getAttribute('value'));
      new PeriodicalExecuter(getRemoteContent, <?=$this->config->item('LIGHT_REFRESH')?>);
	  })
    })()
  </script>
</head>
