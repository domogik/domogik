(function($) {
    $.create_widget({
        // default options
        options: {
            version: 0.1,
            creator: 'Domogik',
            id: 'dmg_1x1_basicActuatorBinary',
            name: 'Basic widget',
            description: 'Basic widget with border and name',
            type: 'actuator.binary',
            height: 1,
            width: 1,
            displayname: true,
			displayborder: true
        },

        _init: function() {
            var self = this, o = this.options;
            this.element.addClass("icon32-usage-" + o.usage)
                .addClass('clickable')
                .processing();
            this._status = $.getStatus();
            this.element.append(this._status);
            this.element.click(function (e) {self.action();e.stopPropagation();})
                .keypress(function (e) {if (e.which == 13 || e.which == 32) {self.action; e.stopPropagation();}});                    

            this.values = [o.model_parameters.value0, o.model_parameters.value1];
            this.texts = [o.usage_parameters.state0, o.usage_parameters.state1];
            this._initValues(1);
        },
        
        _statsHandler: function(stats) {
            if (stats && stats.length > 0) {
                this.setValue(stats[0].value);
            } else {
                this.setValue(null);
            }
        },
        
        _eventHandler: function(timestamp, value) {
            this.setValue(value);
        },
        
        action: function() {
            var self = this, o = this.options;
            this.element.startProcessingState();
            if (this.currentValue) {
                this.processingValue = (this.currentValue == 0)?1:0;                
            } else { // Current state unknown
                // Suppose the switch currently off
                this.processingValue = 1;
            }
            rest.get(['command', o.devicetechnology, o.deviceaddress, this.values[this.processingValue]],
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
        },

        cancel: function() {
            var self = this, o = this.options;
            this.element.stopProcessingState();
            this._status.displayStatusError();
        },

        /* Valid the processing state */
        valid: function(confirmed) {
            var self = this, o = this.options;
            this.processingValue = null;
            this.element.stopProcessingState();
            if (confirmed) {
                this._status.displayStatusOk();
                this.element.doTimeout( 'resetStatus', state_reset_status, function(){
                    self._status.displayResetStatus();
                });
            } else {
                self._status.displayResetStatus();                
            }
        },
        
        setValue: function(value) {
            if (value != null) {
                if (value == 1 || value.toLowerCase() == this.values[1]) {
                    this.currentValue = 1;
                } else {
                    this.currentValue = 0;
                }                
            } else { // Unknown
                this.currentValue = null;
            }
            this.processingValue = null;
            this.displayValue(this.currentValue);
        },

        displayValue: function(value) {
            var self = this, o = this.options;
            if (value != null) {
                if (value == 1) {
                    this.element.displayIcon('value_1');             
                } else {
                    this.element.displayIcon('value_0');             
                }
                this._status.writeStatus(this.texts[value]);
            } else { // Unknown
                this.element.displayIcon('unknown');                             
                this._status.writeStatus('---');
            }
        }
    });
})(jQuery);