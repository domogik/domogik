function widgetmini_range(widgetmini_id, function_id, widget_usage, min_value, max_value, default_value, unit) {
    var percent_value = (default_value / (max_value - min_value)) * 100;
    $("#range_data").data(function_id, {min : min_value, max : max_value, value : default_value, unit : unit});
    $('#' + widgetmini_id).addClass('widgetmini_range')
        .addClass('closed')
        .attr("tabindex", 0)
	.css('-moz-background-size', '100% ' + percent_value + '%')
        .append("<div class='range_value'>"+ default_value + unit +"</div>")
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
            .addClass('icon32-usage-' + widget_usage)
            .toggle(function () {open_range(function_id)},
                function () {close_range(function_id)});
        $('#' + widgetmini_id + ' .range_plus').click(function () {plus_range(function_id)});
        $('#' + widgetmini_id + ' .range_minus').click(function () {minus_range(function_id)});
}

function widget_range(widget_id, function_id, widget_usage, min_value, max_value, default_value, unit) {
    $('#' + widget_id).addClass('widget_range')
        .addClass('icon32-usage-' + widget_usage);
    $('#' + widget_id + " .up").click(function () {plus_range(function_id)});
    $('#' + widget_id + " .down").click(function () {minus_range(function_id)});
    
    $('#' + widget_id + " .slider").slider({
	range: false,
	min: min_value,
	max: max_value,
	value: default_value,
	slide: function(event, ui) {
		slide_range(function_id, ui.value);
	    }
	});
	$('#' + widget_id + " .value").val(default_value + unit);
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
    $('#widget_' + function_id + " .value").val(data.value+data.unit);
    $('#widget_' + function_id + " .slider").slider('value', data.value);
    var percent_value = (data.value / (data.max - data.min)) * 100;
    $('#widgetmini_' + function_id).css('-moz-background-size', '100% ' + percent_value + '%')
}

function minus_range(function_id) {
    var data = $("#range_data").data(function_id);
    data.value = Math.floor((data.value - 10) / 10) * 10;
    if (data.value < data.min) {data.value = data.min}
    $('#widgetmini_' + function_id + ' .range_value').text(data.value+data.unit);
    $('#widget_' + function_id + " .value").val(data.value+data.unit);
    $('#widget_' + function_id + " .slider").slider('value', data.value);
    var percent_value = (data.value / (data.max - data.min)) * 100;
    $('#widgetmini_' + function_id).css('-moz-background-size', '100% ' + percent_value + '%')
}

function slide_range(function_id, value) {
    var data = $("#range_data").data(function_id);
    data.value = value;
    $('#widgetmini_' + function_id + ' .range_value').text(data.value+data.unit);
    $('#widget_' + function_id + " .value").val(data.value+data.unit);
    var percent_value = (data.value / (data.max - data.min)) * 100;
    $('#widgetmini_' + function_id).css('-moz-background-size', '100% ' + percent_value + '%')
}