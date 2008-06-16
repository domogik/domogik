var updateMusic= function() {
    new Ajax.Request('http://localhost/index.php/piece/update_audio/'+$('idpiece').getAttribute('value'), {
        onSuccess:function(transport) {
            var _json = transport.responseJSON;
            myJsProgressBarHandler.setPercentage('progress',_json.root.temps);
        }
    });
}
