

function widgetmini_binary(widgetmini_id, function_id, widget_usage) {
    $('#' + widgetmini_id).addClass('widgetmini_binary')
        .click(function () {process_binary(function_id)})
        .keypress(function (e) {if (e.which == 13 || e.which == 32) {process_binary(function_id);}})
        .addClass('icon32-usage-' + widget_usage)
        .addClass('binary_0')
        .attr("tabindex", 0);
}

function widget_binary(widget_id, function_id, widget_usage) {
    $('#' + widget_id).addClass('widget_binary')
        .addClass('icon32-usage-' + widget_usage)
        .addClass('binary_0');
    $('#' + widget_id + " .on").click(function () {process_binary(function_id, 1)});
    $('#' + widget_id + " .off").click(function () {process_binary(function_id, 0)});
}

function process_binary(function_id, force) {
    $('#widgetmini_' + function_id).addClass('processing_state');
    $('#widget_' + function_id).addClass('processing_state');
    var status = (force == null) ? 1 : force; 
    setTimeout("feedback_binary(" + function_id + ", " + status + ")",3000);
}

function feedback_binary(function_id, status) {
    var widgetmini_id = 'widgetmini_' + function_id;
    var widget_id = 'widget_' + function_id;
    var oldstatus = (status == 0) ? 1 : 0 ;
    $('#' + widgetmini_id).removeClass('processing_state')
        .addClass('ok_state')
        .removeClass('binary_' + oldstatus)
        .addClass('binary_' + status);
    $('#' + widget_id).removeClass('processing_state')
        .addClass('ok_state')
        .removeClass('binary_' + oldstatus)
        .addClass('binary_' + status);
}