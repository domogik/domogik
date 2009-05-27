const REFRESH_DELAY = 1000 * 30;
const BASE_URL = '/domogik/status/';
const DEVICE_URL = BASE_URL + 'device/'; 

function callbackDevicePower(data) { // allow server to refuse change 
	var prefix = '#device_' + data.id;
	if ($(prefix + '_' + data.power).attr('checked') != 'on') {
		$(prefix + ' .device_power').attr('checked', ''); 
		$(prefix + '_' + data.power).attr('checked', 'on');
	}	
}

// notify changes to server
function updateDevicePower(event, element) { 
	var id = $(this).attr('id').split('_')[1];
	var url = DEVICE_URL + id + '/';
	$.post(url, {power: $(this).val()}, callbackDevicePower, 'json');
}

function refresh() {
	var deviceIds = $.makeArray($('div.device').map(function (index, device) {
		return Number($(device).attr('id').split('_')[1])
	})); 
	$.getJSON(BASE_URL, {devices: deviceIds}, function(data) { 
		$.each(data, function(id, device) {
			callbackDevicePower({id: id, power: device.value});
		});
	});
	setTimeout(refresh, REFRESH_DELAY);
} 
 
jQuery(function($) {
	$('.device_power').change(updateDevicePower);
	refresh();
});
 
