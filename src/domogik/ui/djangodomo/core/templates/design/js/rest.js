function getREST(url, callback) {
    $.ajax({
        type: "GET",
        url: "http://127.0.0.1:8080" + url,
        dataType: "jsonp",
        success: callback,
        error: function(XMLHttpRequest, textStatus, errorThrown) {alert(XMLHttpRequest.readyState + ' ' + XMLHttpRequest.status + ' '+ textStatus + ' '+ errorThrown);}
    });
}