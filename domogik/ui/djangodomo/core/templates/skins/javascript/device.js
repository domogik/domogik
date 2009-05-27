const REFRESH_DELAY = 1000 * 5; //30;
const DEVICE_URL = '/domogik/status/device/' 

function callbackDevicePower(data) { // allow server to refuse change
	$('#device_' + data.id + ' .device_power').attr('checked', ''); 
	$('#device_' + data.id + '_' + data.power).attr('checked', 'on');		
}

function updateDevicePower(event, element) {
	if (element == undefined) {
		element = $(this); // called from event listener
		method = $.post;
	} else {
		element = $(element); // called from refresh
		method = $.get;
	}
	console.log(element);
	var id = element.attr('id').split('_')[1];
	var url = DEVICE_URL + id + '/';
	method(url, {power: element.val()}, callbackDevicePower, 'json');
}
const REFRESH_FUNCTIONS = {
	'.device_power:checked': updateDevicePower
}

function refresh() {
	for (var selector in REFRESH_FUNCTIONS) {
		$(selector).each(REFRESH_FUNCTIONS[selector]);
	}
	setTimeout(refresh, REFRESH_DELAY);
}

jQuery(function($) {
	$('.device_power').change(updateDevicePower)
	refresh();
});


