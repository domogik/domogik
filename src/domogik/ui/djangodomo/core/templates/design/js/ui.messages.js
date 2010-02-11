
function display_message(status, msg) {
    if ($("#messages").length) {
        $("#messages").removeClass().addClass(status).text(msg);
    } else {
        $("<div id='messages' class='" + status + "'>" + msg + "</div>").insertAfter("h1");        
    }
}
