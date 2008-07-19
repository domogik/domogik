<?php
/*
	$LastChangedBy: mschneider $
	$LastChangedDate: 2008-07-19 18:55:17 +0200 (sam. 19 juil. 2008) $
	$LastChangedRevision: 76 $
*/
?>
<body>
    <div id="conteneur">
    	<input type="hidden" id="roomId" value="<?=$room?>"/>

      <div id="header">
        Mon Header
      </div>
      <div id="haut">
       </div>
      <div id="gauche">
        <ul id="menuhaut">
        <?
            foreach($menu as $id=>$name)
            {
                echo "<li><a href=\"".$this->config->item('base_url')."index.php/piece/lookup/".$id."\">".$name."</a></li>";
            }
        ?>
     </ul>
      </div>
      <div id="droite">
        
      <ul id="menudroit">
        <?
        $cap = $this->config->item('CAPACITIES');
        foreach($capacities as $c)
        {
            echo "<li><a href=\"".$this->config->item('base_url')."index.php/piece/".$cap[$c]."/".$room."\">".$c."</a></li>";
        }
        ?>
        </ul>
          </div>
      <div id="centre">
      	<div id="titre">
      		<h2>
      			<center>
      			<?=$name_room?>	
				</center>
      		</h2>
			
      	</div>
		<center>
		

