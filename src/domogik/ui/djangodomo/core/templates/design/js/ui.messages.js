
function display_message(status, msg) {
    $("<div id='messages' class='" + status + "'>" + msg + "</div>").insertAfter("h1");
}
