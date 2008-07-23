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

var update = function(transport) {
            var _json = transport.responseJSON;
            myJsProgressBarHandler.setPercentage('progress',_json.root.temps_percent);
            $('duree').update(_json.root.duree+' / '+_json.root.temps_min);
            $('container').firstDescendant().update(_json.root.titre);
            var playh = "";
            var pauseh = "";
            var stoph = "";
            var playcb = "playMusic()";
            var pausecb = "pauseMusic()";
            var stopcb = "stopMusic()";
            switch(_json.root.etat) {
                case "pause":
                    pauseh = "_hidden";
                    pausecb="";
                    break;
                case "stop":
                    pauseh = "_hidden";
                    pausecb="";
                    stoph = "_hidden";
                    stopcb="";
                    break;
                case "play":
                    playh = "_hidden";
                    playcb="";
                    break;
            }
            $('play').setAttribute('src',IMAGES_DIR+'play'+playh+'.png');
            $('pause').setAttribute('src',IMAGES_DIR+'pause'+pauseh+'.png');
            $('stop').setAttribute('src',IMAGES_DIR+'stop'+stoph+'.png');
            $('play').setAttribute('onClick',playcb);
            $('pause').setAttribute('onClick',pausecb);
            $('stop').setAttribute('onClick',stopcb);
}


var updateMusic= function() {
    new Ajax.Request(BASE_URL+'index.php/update/musique/'+$('idpiece').getAttribute('value'), { onSuccess:update });
}

var playMusic = function() {
    new Ajax.Request(BASE_URL+'index.php/musique/play/'+$('idpiece').getAttribute('value'), { onSuccess:update });
}

var pauseMusic = function() {
    new Ajax.Request(BASE_URL+'index.php/musique/pause/'+$('idpiece').getAttribute('value'), { onSuccess:update });
}

var stopMusic = function() {
    new Ajax.Request(BASE_URL+'index.php/musique/stop/'+$('idpiece').getAttribute('value'), { onSuccess:update});
}
