(function($) {
    $.create_widget_1x1_extended({
        // default options
        options: {
            version: 0.1,
            creator: 'Domogik',
            id: 'dmg_1x1_basicActuatorRange',
            name: 'Basic widget',
            description: 'Basic widget with border and name',
            type: 'actuator.range',
            height: 1,
            width: 1,
            // For 1x1 Extended widget
            isOpenable: true,
            hasStatus: true
        },

        _init: function() {
            var self = this, o = this.options;
            this.min_value = parseInt(o.model_parameters.valueMin);
            this.max_value = parseInt(o.model_parameters.valueMax);
            this.step = parseInt(o.usage_parameters.step);
            this.unit = o.usage_parameters.unit
            this._indicator = $("<canvas class='indicator' width='110' height='110'></canvas>");
            this.element.append(this._indicator);
            this._button_max = this._addButtonIcon("range_max", "upright", "icon16-action-max", function (e) {self.max_range();e.stopPropagation();});
            this._button_plus = this._addButtonIcon("range_plus", "rightup", "icon16-action-up", function (e) {self.plus_range();e.stopPropagation();});
            this._button_minus = this._addButtonIcon("range_minus", "rightdown", "icon16-action-down", function (e) {self.minus_range();e.stopPropagation();});
            this._button_min = this._addButtonIcon("range_min", "downright", "icon16-action-min", function (e) {self.min_range();e.stopPropagation();});

			this.element.addClass('closed');
			this.element.append(this._button_plus)
				.append(this._button_minus)
				.append(this._button_max)
				.append(this._button_min);
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
            this.setValue(null);
        },
        
        action: function() {
            var self = this, o = this.options;
            if (this._processingValue != this.currentValue) {
                $.getREST(['command', o.devicetechnology, o.deviceaddress, o.model_parameters.command, this._processingValue],
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

        open: function() {
            if (!this.isOpen) {
                this._open();
                this._processing_percent_current = 0;
                this._setProcessingValue(this._processingValue);
            }
        },
            
        close: function() {
            if (this.isOpen) {
                this._close();
                this.setValue(this.currentValue);
            }
        },
        
        setValue: function(value) {
            var self = this, o = this.options;
            if (value) {
                if (value >= this.min_value && value <= this.max_value) {
                    this.currentValue = value;
                } else if (value < this.min_value) {
                    this.currentValue = this.min_value;
                } else if (value > this.max_value) {
                    this.currentValue = this.max_value
                }
                this._processingValue = this.currentValue;
                var percent = (this.currentValue / (this.max_value - this.min_value)) * 100;
                this._displayIcon('range_' + findRangeIcon(o.usage, percent));
                this._displayValue(this.currentValue);
            } else { // unknown
                this._processingValue = 0;
                this._displayIcon('unknown');
                this._displayValue(null);
            }
        },

		plus_range: function() {
            var self = this, o = this.options;
			var value = ((this._processingValue + this.step) / this.step) * this.step;
      		this._resetAutoClose();
			this._setProcessingValue(value);
		},
		
		minus_range: function() {
            var self = this, o = this.options;
			var value = ((this._processingValue - this.step) / this.step) * this.step;
      		this._resetAutoClose();
			this._setProcessingValue(value);
		},
		
		max_range: function() {
            var self = this, o = this.options;
      		this._resetAutoClose();
			this._setProcessingValue(this.max_value);
		},
		
		min_range: function() {
            var self = this, o = this.options;
      		this._resetAutoClose();
			this._setProcessingValue(this.min_value);
		},
		
		_resetAutoClose: function() {
			var self = this;
			this.element.doTimeout( 'timeout', close_with_change, function(){
				self.action();
                self.close();
			});	
		},
        
        _displayValue: function(value) {
            var self = this, o = this.options;
            if (value) {
    			this._writeStatus(value + this.unit);                
            } else { // Unknown
    			this._writeStatus('---' + this.unit);                                
            }
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
            this._writeStatus(this._processingValue + this.unit);
            this._displayProcessingRange(percent);
		},

        _displayProcessingRange: function(percent) {
            var self = this, o = this.options;
            this._processing_percent_final = percent;
            if (!this._processing_animation) {
                this._animateProcessingRange();
            }
        },

        _animateProcessingRange: function() {
            var self = this, o = this.options;
            this._processing_animation = true;
            if (this._processing_percent_final < this._processing_percent_current) {
                this._processing_percent_current--;
            } else if (this._processing_percent_final > this._processing_percent_current) {
                this._processing_percent_current++;                
            }
            
            var canvas = this._indicator.get(0);
            if (canvas.getContext){
                var ctx = canvas.getContext('2d');
                canvas.width = canvas.width; //reset
                ctx.beginPath();
                ctx.clearRect(0,0, canvas.width, canvas.height);

                if (this._processing_percent_current > 0) {
                    ctx.lineWidth = 10;
                    ctx.strokeStyle = "#BDCB2F";
                    var deg = ((this._processing_percent_current * 360) / 100) - 90;
                    var angle = (Math.PI/180) * deg; // radian
                    ctx.arc(55,55,50,(Math.PI/2),-angle, true);
                    ctx.stroke();                
                }
            }
            
            if (this._processing_percent_final == this._processing_percent_current) { // End animation
                this._processing_animation = false;
            } else {
                setTimeout(function() {self._animateProcessingRange();}, 5);
            }
        },
        
        cancel: function() {
            this.setValue(this.currentValue);
            this._super();
        },
        
        /* Valid the processing state */
        valid: function(confirmed) {
            this._super();
            this.setValue(this._processingValue);
        }
        
    });
})(jQuery);