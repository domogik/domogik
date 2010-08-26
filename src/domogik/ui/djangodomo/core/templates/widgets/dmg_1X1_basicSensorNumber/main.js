(function($) {
    $.create_widget_1x1_extended({
        // default options
        options: {
            version: 0.1,
            creator: 'Domogik',
            id: 'dmg_1x1_basicSensorNumber',
            name: 'Basic widget',
            description: 'Basic widget with border and name',
            type: 'sensor.number',
            height: 1,
            width: 1,
            // For 1x1 Extended widget
            isOpenable: false,
            hasStatus: true,
            hasAction: false,
            namePosition: 'nametopleft'
        },

        _init: function() {
            var self = this, o = this.options;
            /*            
            this._button_day = this._addButtonText("graph_day", "upright", "icon16-action-graph", "Day", function (e) {self._showGraphDay();e.stopPropagation();});
            this._button_month = this._addButtonText("graph_month", "rightup", "icon16-action-graph", "Month", function (e) {self._showGraphMonth();e.stopPropagation();});
            this._button_year = this._addButtonText("graph_year", "right", "icon16-action-graph", "Year", function (e) {self._showGraphYear();e.stopPropagation();});
            */
            this._initValues(1);
        },

        _statsHandler: function(stats) {
            if (stats && stats.length > 0) {
                this.setValue(stats[0].value);
            } else {
                this.setValue(null);
            }
        },
        
        _eventHandler: function(date, value) {
            this.setValue(value);
        },

        setValue: function(value, previous) {
            var self = this, o = this.options;
            if (value) {
                this._displayIcon('number');             
                this._elementValue.html(value + '<br />' + o.model_parameters.unit)
                if (this.previousValue) {
                    if (value == this.previousValue) {
                        this._elementStatus.attr('class', 'status icon8-status-equal')
                        this._elementStatus.html("<span class='offscreen'>linear</span>");
                    } else if (value > this.previousValue) {
                        this._elementStatus.attr('class', 'status icon8-status-up')
                        this._elementStatus.html("<span class='offscreen'>going up</span>");
                    } else {
                        this._elementStatus.attr('class', 'status icon8-status-down')
                        this._elementStatus.html("<span class='offscreen'>going down</span>");
                    }
                }
            } else { // Unknown
                this._displayIcon('unknown');             
                this._elementValue.html('--<br />' + o.model_parameters.unit)
            }
            this.previousValue = value;
        },

        _showGraphDay: function() {
            var self = this, o = this.options;
            this.close();
            var now = new Date();
            var from = Math.round(new Date(now.getFullYear(), now.getMonth(), now.getDate(),0,0,0).getTime() / 1000);
            var to = Math.round(new Date(now.getFullYear(), now.getMonth(), now.getDate(),23,59,59).getTime() / 1000);
            $.getREST(['stats', o.deviceid, o.key, 'from', from],
                function(data) {
                    var status = (data.status).toLowerCase();
                    if (status == 'ok') {
                        var d = [];
                        $.each(data.stats, function(index, stat) {
                            d.push([(stat.date*1000), stat.value]);
                        });
                        var dialog = $("<div id='dialog' title='Graph Day'><div id='graph' style='width:600px;height:300px;'></div></div>");
                        $('body').append(dialog);
                        dialog.dialog({ height: 340, width:640,
                                        resizable: false,
                                        modal: true,
                                        close: function(ev, ui) {
                                            $(this).remove();
                                        }
                                    });
                        
                        $.plot($("#graph"), [d], {
                              xaxis: {
                                mode: "time",
                                timeformat: "%h:%M",
                                min: (from*1000),
                                max: (to*1000)
                              }
                        });
                    } else {
                        $.notification('error', '{% trans "data creation failed" %} (' + data.description + ')');                                                                      
                    }
                }
            );
        },
        
        _showGraphMonth: function() {
            var self = this, o = this.options;
            this.close();
            var now = new Date();
            var from = Math.round(new Date(now.getFullYear(), now.getMonth(), 1, 0, 0, 0).getTime() / 1000);
            var to = Math.round(new Date(now.getFullYear(), now.getMonth(), 31 ,23,59,59).getTime() / 1000);
            $.getREST(['stats', o.deviceid, o.key, 'from', from],
                function(data) {
                    var status = (data.status).toLowerCase();
                    if (status == 'ok') {
                        var d = [];
                        $.each(data.stats, function(index, stat) {
                            d.push([(stat.date*1000), stat.value]);
                        });
                        var dialog = $("<div id='dialog' title='Graph Month'><div id='graph' style='width:600px;height:300px;'></div></div>");
                        $('body').append(dialog);
                        dialog.dialog({ height: 340, width:640,
                                        resizable: false,
                                        modal: true,
                                        close: function(ev, ui) {
                                            $(this).remove();
                                        }
                                    });
                        
                        $.plot($("#graph"), [d], {
                              xaxis: {
                                mode: "time",
                                timeformat: "%d",
                                min: (from*1000),
                                max: (to*1000)
                              }
                        });
                    } else {
                        $.notification('error', '{% trans "data creation failed" %} (' + data.description + ')');                                                                      
                    }
                }
            );
        },
        
        _showGraphYear: function() {
            var self = this, o = this.options;
            this.close();
            var now = new Date();
            var from = Math.round(new Date(now.getFullYear(), 0, 1, 0, 0, 0).getTime() / 1000);
            var to = Math.round(new Date(now.getFullYear(), 11, 31 ,23,59,59).getTime() / 1000);
            $.getREST(['stats', o.deviceid, o.key, 'from', from],
                function(data) {
                    var status = (data.status).toLowerCase();
                    if (status == 'ok') {
                        var d = [];
                        $.each(data.stats, function(index, stat) {
                            d.push([(stat.date*1000), stat.value]);
                        });
                        var dialog = $("<div id='dialog' title='Graph Year'><div id='graph' style='width:600px;height:300px;'></div></div>");
                        $('body').append(dialog);
                        dialog.dialog({ height: 340, width:640,
                                        resizable: false,
                                        modal: true,
                                        close: function(ev, ui) {
                                            $(this).remove();
                                        }
                                    });
                        
                        $.plot($("#graph"), [d], {
                              xaxis: {
                                mode: "time",
                                timeformat: "%b",
                                monthNames: ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"],
                                min: (from*1000),
                                max: (to*1000)
                              }
                        });
                    } else {
                        $.notification('error', '{% trans "data creation failed" %} (' + data.description + ')');                                                                      
                    }
                }
            );
        }
    });
})(jQuery);

/*
 * Date Format 1.2.3
 * (c) 2007-2009 Steven Levithan <stevenlevithan.com>
 * MIT license
 *
 * Includes enhancements by Scott Trenda <scott.trenda.net>
 * and Kris Kowal <cixar.com/~kris.kowal/>
 *
 * Accepts a date, a mask, or a date and a mask.
 * Returns a formatted version of the given date.
 * The date defaults to the current date/time.
 * The mask defaults to dateFormat.masks.default.
 */

var dateFormat = function () {
	var	token = /d{1,4}|m{1,4}|yy(?:yy)?|([HhMsTt])\1?|[LloSZ]|"[^"]*"|'[^']*'/g,
		timezone = /\b(?:[PMCEA][SDP]T|(?:Pacific|Mountain|Central|Eastern|Atlantic) (?:Standard|Daylight|Prevailing) Time|(?:GMT|UTC)(?:[-+]\d{4})?)\b/g,
		timezoneClip = /[^-+\dA-Z]/g,
		pad = function (val, len) {
			val = String(val);
			len = len || 2;
			while (val.length < len) val = "0" + val;
			return val;
		};

	// Regexes and supporting functions are cached through closure
	return function (date, mask, utc) {
		var dF = dateFormat;

		// You can't provide utc if you skip other args (use the "UTC:" mask prefix)
		if (arguments.length == 1 && Object.prototype.toString.call(date) == "[object String]" && !/\d/.test(date)) {
			mask = date;
			date = undefined;
		}

		// Passing date through Date applies Date.parse, if necessary
		date = date ? new Date(date) : new Date;
		if (isNaN(date)) throw SyntaxError("invalid date");

		mask = String(dF.masks[mask] || mask || dF.masks["default"]);

		// Allow setting the utc argument via the mask
		if (mask.slice(0, 4) == "UTC:") {
			mask = mask.slice(4);
			utc = true;
		}

		var	_ = utc ? "getUTC" : "get",
			d = date[_ + "Date"](),
			D = date[_ + "Day"](),
			m = date[_ + "Month"](),
			y = date[_ + "FullYear"](),
			H = date[_ + "Hours"](),
			M = date[_ + "Minutes"](),
			s = date[_ + "Seconds"](),
			L = date[_ + "Milliseconds"](),
			o = utc ? 0 : date.getTimezoneOffset(),
			flags = {
                D:    D,
				d:    d,
				dd:   pad(d),
				ddd:  dF.i18n.dayNames[D],
				dddd: dF.i18n.dayNames[D + 7],
				m:    m + 1,
				mm:   pad(m + 1),
				mmm:  dF.i18n.monthNames[m],
				mmmm: dF.i18n.monthNames[m + 12],
				yy:   String(y).slice(2),
				yyyy: y,
				h:    H % 12 || 12,
				hh:   pad(H % 12 || 12),
				H:    H,
				HH:   pad(H),
				M:    M,
				MM:   pad(M),
				s:    s,
				ss:   pad(s),
				l:    pad(L, 3),
				L:    pad(L > 99 ? Math.round(L / 10) : L),
				t:    H < 12 ? "a"  : "p",
				tt:   H < 12 ? "am" : "pm",
				T:    H < 12 ? "A"  : "P",
				TT:   H < 12 ? "AM" : "PM",
				Z:    utc ? "UTC" : (String(date).match(timezone) || [""]).pop().replace(timezoneClip, ""),
				o:    (o > 0 ? "-" : "+") + pad(Math.floor(Math.abs(o) / 60) * 100 + Math.abs(o) % 60, 4),
				S:    ["th", "st", "nd", "rd"][d % 10 > 3 ? 0 : (d % 100 - d % 10 != 10) * d % 10]
			};

		return mask.replace(token, function ($0) {
			return $0 in flags ? flags[$0] : $0.slice(1, $0.length - 1);
		});
	};
}();

// Some common format strings
dateFormat.masks = {
	"default":      "ddd mmm dd yyyy HH:MM:ss",
	shortDate:      "m/d/yy",
	mediumDate:     "mmm d, yyyy",
	longDate:       "mmmm d, yyyy",
	fullDate:       "dddd, mmmm d, yyyy",
	shortTime:      "h:MM TT",
	mediumTime:     "h:MM:ss TT",
	longTime:       "h:MM:ss TT Z",
	isoDate:        "yyyy-mm-dd",
	isoTime:        "HH:MM:ss",
	isoDateTime:    "yyyy-mm-dd'T'HH:MM:ss",
	isoUtcDateTime: "UTC:yyyy-mm-dd'T'HH:MM:ss'Z'"
};

// Internationalization strings
dateFormat.i18n = {
	dayNames: [
		"Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat",
		"Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"
	],
	monthNames: [
		"Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
		"January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"
	]
};

// For convenience...
Date.prototype.format = function (mask, utc) {
	return dateFormat(this, mask, utc);
};
