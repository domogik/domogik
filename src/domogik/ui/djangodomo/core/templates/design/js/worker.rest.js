importScripts("/design/js/jquery-1.4.2.min.js")
    
// Triggered by postMessage in the page
onmessage = function (evt) {
    var rest_url = evt.data.url;
    // Build the REST url
    $.each(evt.data.parameters, function(){
        rest_url += '/' + encodeURIComponent(this);     
    });
    
    $.ajax({
        type: "GET",
        url: rest_url,
        dataType: "jsonp",
        success:
            evt.data.callback,
        error:
            function(XMLHttpRequest, textStatus, errorThrown) {
//                $.reloadPage({'status': 'error', 'msg': 'REST Error : ' + XMLHttpRequest.readyState + ' ' + XMLHttpRequest.status + ' ' + textStatus + ' ' + errorThrown});
            }
    });
};

