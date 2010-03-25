
function display_message(status, msg) {
    if ($("#messages").length) {
        $("#messages").removeClass().addClass(status.toLowerCase()).text(msg);
    } else {
        $("<div id='messages' class='" + status.toLowerCase() + " icon32-status-" + status.toLowerCase() + "'>" + msg + "</div>").insertAfter("h1");        
    }
}
