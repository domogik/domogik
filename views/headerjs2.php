	
    <script src="<?=$this->config->item('JS_DIR')?>prototype.js" language="JavaScript" ></script>
	<script src="<?=$this->config->item('JS_DIR')?>reflection.js" type="text/javascript" ></script>
<script type="text/javascript" src="/include/flotr/flotr.js" ></script>
<script>
var f = null;       
var load = function(){
    new Ajax.Request('http://localhost/index.php/piece/update/'+$('idpiece').getAttribute('value'), {
        onSuccess: function(transport){
            /**
             * Parse (eval) the JSON from the server.
             */
            var json = transport.responseText.evalJSON();
            
            if(json.series && json.options){
                /**
                 * The json is valid! Display the canvas container.
                 */
                $('container').setStyle({'display':'block'});
                
                /**
                 * Draw the graph using the JSON data. Of course the
                 * options are optional.
                 */
                var f = Flotr.draw($('container'), json.series, json.options);
            }
        }
    });
}
</script>
  	<script type="text/javascript" charset="utf-8">

	/*
	 * Chargement de la page
	 */
	(function() {
      Event.observe(document, 'dom:loaded', function() {
	    load();
        new PeriodicalExecuter(load, <?=$this->config->item('TEMP_REFRESH')?>);
	  })
    })()
  </script>
</head>
