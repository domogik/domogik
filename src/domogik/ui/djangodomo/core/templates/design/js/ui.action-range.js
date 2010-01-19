function widgetmini_range(widgetmini_id, function_id, widget_type, min_value, max_value, default_value, unit) {
    $("#range_data").data(function_id, {min : min_value, max : max_value, value : default_value, unit : unit});
    $('#' + widgetmini_id).addClass('widgetmini_range')
        .addClass('icon32-widget-' + widget_type)
        .addClass('closed')
        .attr("tabindex", 0)
        .append("<span class='range_value'>"+ default_value + unit +"</span>")
        .append("<div class='range_plus' style='display:none'></div>")
		.append("<div class='range_minus' style='display:none'></div>")
        .keypress(function (e) {
            switch(e.keyCode) { 
            // User pressed "up" arrow
            case 38:
                plus_range(function_id);
                break;
            // User pressed "down" arrow
            case 40:
                minus_range(function_id);
                break;
            }
        });

        $('#' + widgetmini_id + ' .range_value')
            .toggle(function () {open_range(function_id)},
                function () {close_range(function_id)});
        $('#' + widgetmini_id + ' .range_plus').click(function () {plus_range(function_id)});
        $('#' + widgetmini_id + ' .range_minus').click(function () {minus_range(function_id)});
}

function open_range(function_id) {
    $('#widgetmini_' + function_id).removeClass('closed')
    .addClass('opened');
    $('#widgetmini_' + function_id + ' .range_plus, #widgetmini_' + function_id + ' .range_minus').show();
}

function close_range(function_id) {
    $('#widgetmini_' + function_id).removeClass('opened')
    .addClass('closed');
    $('#widgetmini_' + function_id + ' .range_plus, #widgetmini_' + function_id + ' .range_minus').hide();
}

function plus_range(function_id) {
    var data = $("#range_data").data(function_id);
    data.value = Math.floor((data.value + 10) / 10) * 10;
    if (data.value > data.max) {data.value = data.max}
    $('#widgetmini_' + function_id + ' .range_value').text(data.value+data.unit);
}

function minus_range(function_id) {
    var data = $("#range_data").data(function_id);
    data.value = Math.floor((data.value - 10) / 10) * 10;
    if (data.value < data.min) {data.value = data.min}
    $('#widgetmini_' + function_id + ' .range_value').text(data.value+data.unit);
}