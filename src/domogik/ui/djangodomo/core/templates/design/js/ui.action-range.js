const close_without_change = 10000; // 10 seconds
const close_with_change = 3000; // 3 seconds
const range_reset_status = 4000; // 4 seconds

(function($) {
	$.widget("ui.range_command", {
        _init: function() {
            var self = this, o = this.options;
            this.min_value = parseInt(o.min_value);
            this.max_value = parseInt(o.max_value);
            this.step = parseInt(o.step);
            this.element.range_widget_core({
                usage: o.usage,
                isCommand: true
            })
                .attr("tabindex", 0);
			this.button_plus = $("<div class='range_plus' style='display:none'></div>");
			this.button_plus.click(function (e) {self.plus_range();e.stopPropagation()});
			this.button_minus = $("<div class='range_minus' style='display:none'></div>");
			this.button_minus.click(function (e) {self.minus_range();e.stopPropagation()});
			this.button_max = $("<div class='range_max' style='display:none'></div>");
			this.button_max.click(function (e) {self.max_range();e.stopPropagation()});
			this.button_min = $("<div class='range_min' style='display:none'></div>");
			this.button_min.click(function (e) {self.min_range();e.stopPropagation()});
			this.element.addClass('closed');
			this.element.find('.widget_icon').append(this.button_plus)
				.append(this.button_minus)
				.append(this.button_max)
				.append(this.button_min)
				.click(function (e) {
						if (self.openflag) {
							self.close();
							self.processValue();							
						} else {
							self.open();							
						}
						e.stopPropagation();
					});
			this.element.keypress(function (e) {
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
					e.stopPropagation();
				});
        },

		setValue: function(value) {
            var self = this, o = this.options;
			if (value >= this.min_value && value <= this.max_value) {
				this.currentValue = value;
			} else if (value < this.min_value) {
				this.currentValue = this.min_value;
			} else if (value > this.max_value) {
				this.currentValue = this.max_value
			}
			this.processingValue = this.currentValue;
			var percent = (this.currentValue / (this.max_value - this.min_value)) * 100;
			var icon = 'range_' + findRangeIcon(o.usage, percent);

            this.displayValue(this.currentValue, icon, this.currentIcon);
			this.currentIcon = icon;
        },

		setProcessingValue: function(value) {
            var self = this, o = this.options;
			if (value >= this.min_value && value <= this.max_value) {
				this.processingValue = value;
			} else if (value < this.min_value) {
				this.processingValue = this.min_value;
			} else if (value > this.max_value) {
				this.processingValue = this.max_value
			}
			var percent = (this.processingValue / (this.max_value - this.min_value)) * 100;
            this.displayProcessingValue(this.processingValue, percent);
		},
		
		processValue: function() {
			if (this.processingValue != this.currentValue) { // If the value was changed
                this.element.range_widget_core('startProcessingState');
				this.options.action(this, this.processingValue);				
			}
		},
		
		displayRangeIcon: function(newIcon, previousIcon) {
			if (previousIcon) {
				this.element.removeClass(previousIcon);				
			}
			this.element.addClass(newIcon);
        },
		

        displayValue: function(value, newIcon, previousIcon) {
            this.element.range_widget_core('displayRangeIcon', newIcon, previousIcon);                
            this.element.range_widget_core('displayValue', value, this.options.unit);                
        },
		
        displayProcessingValue: function(value, percent) {
            this.element.range_widget_core('displayBackground', percent);
            this.element.range_widget_core('displayProcessingValue', value, this.options.unit);                
        },
		
		plus_range: function() {
            var self = this, o = this.options;
			var value = ((this.processingValue + this.step) / this.step) * this.step;
      		this.resetAutoClose();
			this.setProcessingValue(value);
		},
		
		minus_range: function() {
            var self = this, o = this.options;
			var value = ((this.processingValue - this.step) / this.step) * this.step;
      		this.resetAutoClose();
			this.setProcessingValue(value);
		},
		
		max_range: function() {
            var self = this, o = this.options;
      		this.resetAutoClose();
			this.setProcessingValue(this.max_value);
		},
		
		min_range: function() {
            var self = this, o = this.options;
      		this.resetAutoClose();
			this.setProcessingValue(this.min_value);
		},
		
		resetAutoClose: function() {
			var self = this;
			this.element.doTimeout( 'timeout', close_with_change, function(){
                self.close();
				self.processValue();
			});	
		},
        
        open: function() {
			var self = this;
			this.openflag = true;
			this.element.removeClass('closed')
				.addClass('opened');
			this.button_plus.show();
			this.button_minus.show();
			this.button_max.show();
			this.button_min.show();
			this.displayProcessingValue(this.currentValue);
			this.element.doTimeout( 'timeout', close_without_change, function(){
				self.close();
			});
		},
		
		close: function() {
			this.openflag = false;
			this.element.removeClass('opened')
				.addClass('closed');
			this.button_plus.hide();
			this.button_minus.hide();
			this.button_max.hide();
			this.button_min.hide();
		},
        
        cancel: function() {
			this.processingValue = this.currentValue;
            this.element.range_widget_core('stopProcessingState');
            setValue(this.currentValue);
            this.element.range_widget_core('displayStatusError');
        },
        
        /* Valid the processing state */
        valid: function(confirmed) {
            var self = this, o = this.options;
            this.element.range_widget_core('stopProcessingState');
            if (confirmed) {
                this.element.range_widget_core('displayStatusOk');
                this.element.doTimeout( 'resetStatus', range_reset_status, function(){
                    self.element.range_widget_core('displayResetStatus');
    			});
            }
            setValue(this.processingValue);
        }
		
	});
    
    $.extend($.ui.range_command, {
        defaults: {
        }
    });
	
	/* Widget */
    
    $.widget("ui.range_widget_core", {
        _init: function() {
            var self = this, o = this.options;
            this.element.addClass('widget_range');
            this.elementicon = $("<div class='widget_icon'></div>");
			this.elementvalue = $("<div class='widget_value'></div>");
            this.elementvalue.addClass('icon32-state-' + o.usage);                
			this.elementicon.append(this.elementvalue);				
            this.element.append(this.elementicon);
            if(o.isCommand) {
    			this.elementstate = $("<div class='widget_state'></div>");
    			this.elementvalue.append(this.elementstate);
                this.element.addClass('command');
                this.elementicon.processing();
            } else {
    			this.elementvalue.addClass('range_100');
            }
			this.displayBackground(0);
        },

		displayBackground: function(percent) {
			this.elementicon.css('-moz-background-size', '100% ' + percent + '%');
			this.elementicon.css('-webkit-background-size', '100% ' + percent + '%');
        },

		displayRangeIcon: function(newIcon, previousIcon) {
			if (previousIcon) {
				this.elementvalue.removeClass(previousIcon);				
			}
			this.elementvalue.addClass(newIcon);
        },
		
		displayValue: function(value, unit) {
			this.elementstate.text(value + unit);
			this.elementicon.css('-moz-background-size', '0');
			this.elementicon.css('-webkit-background-size', '0');
        },
		
		displayProcessingValue: function(value, unit) {
			this.elementstate.text(value + unit);
		},
        
        displayStatusError: function() {
            this.elementstate.addClass('error');
        },
        
        displayStatusOk: function() {
            this.elementstate.addClass('ok');
        },
        
        displayResetStatus: function() {
            this.elementstate.removeClass('ok');
        },
        
        startProcessingState: function() {
            this.elementicon.processing('start');
        },
        
        stopProcessingState: function() {
            this.elementicon.processing('stop');
        }

    });
    
    $.extend($.ui.range_widget_core, {
        defaults: {
			isCommand: true
        }
    });
})(jQuery);