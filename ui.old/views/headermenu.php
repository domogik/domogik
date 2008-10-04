<?php
/*
Copyright 2008 Domogik project

This file is part of Domogik.
Domogik is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Domogik is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Domogik.  If not, see <http://www.gnu.org/licenses/>.

Author: Maxence Dunnewind <maxence@dunnewind.net>

$LastChangedBy: mschneider $
$LastChangedDate: 2008-07-23 21:42:29 +0200 (mer. 23 juil. 2008) $
$LastChangedRevision: 100 $
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
		

