const REFRESH_DELAY = 1000 * 30;
const BASE_URL = '/domogik/status/';
const DEVICE_URL = BASE_URL + 'device/'; 
const INCREASE_OFFSET = 5;
const MIN_VALUE = 0;
const MAX_VALUE = 100;


function callbackDevicePower(data) { // allow server to refuse change 
	var prefix = '#device_' + data.id + ' ';
	
	if (data.type == "lamp") {
		$(prefix + ".device_value").val(data.value);
		if (Number(data.value) == 0) {
			data.value = "off";
		} else {
			data.value = "on";
		}
	}
	
	if ($(prefix + '.power_' + data.value).attr('checked') != 'on') {
		$(prefix + '.device_power').attr('checked', ''); 
		$(prefix + '.power_' + data.value).attr('checked', 'on');
	}	
}

function updateDevicePower() { // notify changes to server
	var id = $(this).parent('div.device').attr('id').split('_')[1];
	var url = DEVICE_URL + id + '/';
	var hasChanged = true;
	
	if ($(this).hasClass('device_scale')) {
		var target = $(this).siblings('.device_value');
		var oldValue = Number(target.val());
		if ($(this).hasClass('device_increase')) {
			var newValue = oldValue + INCREASE_OFFSET;
			if (newValue > MAX_VALUE) newValue = MAX_VALUE;
		} else {
			var newValue = oldValue - INCREASE_OFFSET;
			if (newValue < MIN_VALUE) newValue = MIN_VALUE;	
		}
		if (newValue == oldValue) hasChanged = false;
		target.val(newValue);
		datas = {value: newValue};
	} else {
		datas = {value: $(this).val()};
	}
	if (hasChanged) {
		$.post(url, datas, callbackDevicePower, 'json');		
	}
}

function refresh() {
	var deviceIds = $.makeArray($('div.device').map(function (index, device) {
		return Number($(device).attr('id').split('_')[1])
	})); 
	$.getJSON(BASE_URL, {devices: deviceIds}, function(data) { 
		$.each(data, function(id, device) {
			callbackDevicePower({id: id, value: device.value});
		});
	});
	setTimeout(refresh, REFRESH_DELAY);
} 
 
jQuery(function($) {
	$('.device_power').change(updateDevicePower);
	$('.device_scale').click(updateDevicePower); 
	refresh();
});
 
