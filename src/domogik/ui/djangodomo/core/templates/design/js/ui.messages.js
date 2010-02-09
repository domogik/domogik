
function display_message(status, msg) {
    $("<div class='action-message " + status + "'>" + msg + "</div>").insertAfter("h1");
}
