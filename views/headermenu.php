<body>
    <div id="conteneur">
    	<input type="hidden" id="idpiece" value="<?=$piece?>"/>

      <div id="header">
        Mon Header
      </div>
      <div id="haut">
       </div>
      <div id="gauche">
        <ul id="menuhaut">
        <?
            foreach($menu as $id=>$nom)
            {
                echo "<li><a href=\"".$this->config->item('base_url')."index.php/piece/lookup/".$id."\">".$nom."</a></li>";
            }
        ?>
     </ul>
      </div>
      <div id="droite">
        
      <ul id="menudroit">
        <? 
        $cap = $this->config->item('CAPACITIES');
        foreach($capacites as $c)
        {
            echo "<li><a href=\"".$this->config->item('base_url')."index.php/piece/".$cap[$c]."/".$piece."\">".$c."</a></li>";
        }
        ?>
        </ul>
          </div>
      <div id="centre">
      	<div id="titre">
      		<h2>
      			<center>
      			<?=$name_piece?>	
				</center>
      		</h2>
			
      	</div>
		<center>
		

