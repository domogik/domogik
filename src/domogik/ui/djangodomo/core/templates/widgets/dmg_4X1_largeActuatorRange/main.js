const auto_send = 3000; // 3 seconds

(function($) {
    $.create_widget({
        // default options
        options: {
            version: 0.1,
            creator: 'Domogik',
            id: 'dmg_4X1_largeActuatorRange',
            name: 'Large actuator range',
            description: 'Large actuator range with nice design',
            type: 'actuator.range',
            height: 1,
            width: 4,
            displayname: false,
			displayborder: false
        },

        _init: function() {
            var self = this, o = this.options;
            this.min_value = parseInt(o.model_parameters.valueMin);
            this.max_value = parseInt(o.model_parameters.valueMax);
            this.step = parseInt(o.usage_parameters.step);
            this.unit = o.usage_parameters.unit

            var ident = $("<div class='ident'>" + o.devicename + " - " + o.featurename + "</div>");
            this.element.append(ident);
            var main = $("<div class='main'></div>");
            this.indicator = $("<div class='indicator'></div>");
            main.append(this.indicator);
            this.value = $("<div class='value'></div>");
            main.append(this.value);

            var min = $("<div class='command min'><span class='offscreen'>Min</span></div>");
            min.click(function (e) {self.min_range();e.stopPropagation();});
            main.append(min);
            var minus = $("<div class='command minus'><span class='offscreen'>Minus</span></div>");
            minus.click(function (e) {self.minus_range();e.stopPropagation();});
            main.append(minus);
            var plus = $("<div class='command plus'><span class='offscreen'>Plus</span></div>");
            plus.click(function (e) {self.plus_range();e.stopPropagation();});
            main.append(plus);
            var max = $("<div class='command max'><span class='offscreen'>Max</span></div>");
            max.click(function (e) {self.max_range();e.stopPropagation();});
            main.append(max);
            this.element.append(main);
            this.element.keypress(function (e) {
					e.stopPropagation();
					switch(e.keyCode) { 
					// User pressed "home" key
					case 36:
						self.max_range();
						break;
					// User pressed "end" key
					case 35:
						self.min_range();
						break;
					// User pressed "up" arrow
					case 38:
						self.plus_range();
						break;
					// User pressed "down" arrow
					case 40:
						self.minus_range();
						break;
					}
				});
            this._initValues(1);
        },

        _statsHandler: function(stats) {
            if (stats && stats.length > 0) {
                this.setValue(parseInt(stats[0].value));
            } else {
                this.setValue(null);
            }
        },
        
        _eventHandler: function(date, value) {
            this.setValue(parseInt(value));
        },

        setValue: function(value) {
            var self = this, o = this.options;
            if (value != null) {
                if (value >= this.min_value && value <= this.max_value) {
                    this.currentValue = value;
                } else if (value < this.min_value) {
                    this.currentValue = this.min_value;
                } else if (value > this.max_value) {
                    this.currentValue = this.max_value
                }
                this._processingValue = this.currentValue;
                var percent = (this.currentValue / (this.max_value - this.min_value)) * 100;
                this._displayValue(this.currentValue);
                this._displayRangeIndicator(percent);
            } else { // unknown
                this._processingValue = 0;
                this._displayValue(null);
                this._displayRangeIndicator(0);
            }
        },
        
        action: function() {
            var self = this, o = this.options;
            if (this._processingValue != this.currentValue) {
                this._startProcessingState();
                rest.get(['command', o.devicetechnology, o.deviceaddress, o.model_parameters.command, this._processingValue],
                    function(data) {
                        var status = (data.status).toLowerCase();
                        if (status == 'ok') {
                            self.valid(o.featureconfirmation);
                        } else {
                            /* Error */
                            self.cancel();
                            $.notification('error', data.description);
                        }
                    }
                );
			}
        },
        
        plus_range: function() {
            var self = this, o = this.options;
			var value = ((this._processingValue + this.step) / this.step) * this.step;
			this._setProcessingValue(value);
            this._resetAutoSend();
		},
		
		minus_range: function() {
            var self = this, o = this.options;
			var value = ((this._processingValue - this.step) / this.step) * this.step;
			this._setProcessingValue(value);
            this._resetAutoSend();
		},
		
		max_range: function() {
            var self = this, o = this.options;
			this._setProcessingValue(this.max_value);
            this._resetAutoSend();
		},
		
		min_range: function() {
            var self = this, o = this.options;
			this._setProcessingValue(this.min_value);
            this._resetAutoSend();
		},
        
        _setProcessingValue: function(value) {
            var self = this, o = this.options;
			if (value >= this.min_value && value <= this.max_value) {
				this._processingValue = value;
			} else if (value < this.min_value) {
				this._processingValue = this.min_value;
			} else if (value > this.max_value) {
				this._processingValue = this.max_value
			}
			var percent = (this._processingValue / (this.max_value - this.min_value)) * 100;
            this._displayValue(this._processingValue);
            this._displayRangeIndicator(percent);
		},
        
        _displayValue: function(value) {
            var self = this, o = this.options;
            if (value != null) {
                this.value.text(value + this.unit);                
            } else { // Unknown
                this.value.text('---' + this.unit);                                
            }
        },
        
        _displayRangeIndicator: function(percent) {
            var self = this, o = this.options;
            this.indicator.width((23*percent)/100 + "em");
        },
        
        cancel: function() {
            this.setValue(this.currentValue);
            this._stopProcessingState();
        },

        valid: function(confirmed) {
            this._stopProcessingState();
        },
        
        _startProcessingState: function() {
            this.value.addClass('processing');
            this.value.text('');
        },

        _stopProcessingState: function() {
            this.value.removeClass('processing');
        },

        _resetAutoSend: function() {
			var self = this;
			this.element.doTimeout( 'timeout', auto_send, function(){
				self.action();
			});	
		}
    });
})(jQuery);