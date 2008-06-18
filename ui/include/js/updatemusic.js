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
