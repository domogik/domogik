
function display_message(status, msg) {
    $("h1:after").append("<div class='action-message " + status + "'>" + msg + "</div>");
}
