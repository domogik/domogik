const close_without_change = 10000; // 10 seconds
const close_with_change = 3000; // 3 seconds

(function($) {
	$.widget("ui.range_command", {
        _init: function() {
            var self = this, o = this.options;
			var states = o.states.toLowerCase().split(/\s*,\s*/);
			this.min_value = parseInt(states[0]);
			this.max_value = parseInt(states[1]);
			this.steps = parseInt(states[2]);
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
			var self = this;
			if (value >= this.min_value && value <= this.max_value) {
				this.currentValue = value;
			} else if (value < this.min_value) {
				this.currentValue = this.min_value;
			} else if (value > this.max_value) {
				this.currentValue = this.max_value
			}
			this.processingValue = this.currentValue;
			var percent = (this.currentValue / (this.max_value - this.min_value)) * 100;
			var icon = 'range_' + findRangeIcon(this.options.usage, percent);

            this.displayValue(this.currentValue, icon, this.currentIcon);
			this.currentIcon = icon;
        },

		setProcessingValue: function(value) {
			var self = this;
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
			var value = ((this.processingValue + this.steps) / this.steps) * this.steps;
      		this.resetAutoClose();
			this.setProcessingValue(value);
		},
		
		minus_range: function() {
			var value = ((this.processingValue - this.steps) / this.steps) * this.steps;
      		this.resetAutoClose();
			this.setProcessingValue(value);
		},
		
		max_range: function() {
      		this.resetAutoClose();
			this.setProcessingValue(this.max_value);
		},
		
		min_range: function() {
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
		}
    });
    
    $.extend($.ui.range_widget_core, {
        defaults: {
			isCommand: true
        }
    });
})(jQuery);