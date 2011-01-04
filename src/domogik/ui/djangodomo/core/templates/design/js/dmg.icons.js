var area_icons = ["area", "attic", "basement", "basement2", "firstfloor", "firstfloor2", "secondfloor", "secondfloor2", "groundfloor", "groundfloor2", "garden", "garage"];
var room_icons = ["kitchen", "bedroom", "tvlounge", "bathroom", "office", 'kidsroom', 'garage'];

/* Define range how many icon in various ranges */
var range = [];
range['light'] = [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100];
range['appliance'] = [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100];
range['shutter'] = [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100];
range['air_conditionning'] = [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100];
range['ventilation'] = [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100];
range['heating'] = [0, 100];
range['computer'] = [0, 100];
range['server'] = [0, 100];
range['telephony'] = [0, 100];
range['tv'] = [0, 100];
range['water'] = [0, 100];
range['gas'] = [0, 100];
range['electricity'] = [0, 100];
range['temperature'] = [0, 100];
range['mirror'] = [0, 100];
range['nanoztag'] = [0, 100];
range['music'] = [0, 100];

function findRangeIcon(usage, percent) {
	var nearest, last_d_memorized = 101;
	var set = range[usage];
	// We iterate on the array...
	for (var i = 0; i < set.length ;i++) {
		// if we found the desired number, we return it.
		var value = set[i];
		if (value == percent) {
			return value;
		} else {
			// else, we consider the difference between the desired number and the current number in the array.
			var d = Math.abs(percent - value);
			if (d < last_d_memorized) {
				// For the moment, this value is the nearest to the desired number...
				nearest = value;
				last_d_memorized = d; //is the actual shortest found delta 
			}
		}
	}
	return nearest;
}