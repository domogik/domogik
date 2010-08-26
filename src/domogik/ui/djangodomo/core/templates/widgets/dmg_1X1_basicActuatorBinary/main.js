(function($) {
    $.create_widget_1x1_extended({
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
            // For 1x1 Extended widget
            isOpenable: false,
            hasStatus: true,
            namePosition: 'nametop'
        },

        _init: function() {
            var self = this, o = this.options;
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
        
        _eventHandler: function(date, value) {
            this.setValue(value);
        },
        
        action: function() {
            var self = this, o = this.options;
            this._startProcessingState();
            if (this.currentValue) {
                this.processingValue = (this.currentValue == 0)?1:0;                
            } else { // Current state unknown
                // Suppose the switch currently off
                this.processingValue = 1;
            }
            $.getREST(['command', o.devicetechnology, o.deviceaddress, this.values[this.processingValue]],
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
                    this._displayIcon('binary_1');             
                } else {
                    this._displayIcon('binary_0');             
                }
                this._writeStatus(this.texts[value]);
            } else { // Unknown
                this._displayIcon('unknown');                             
                this._writeStatus('---');
            }
        },
        
        cancel: function() {
            this.processingValue = null;
            this._super();
        },

        /* Valid the processing state */
        valid: function(confirmed) {
            this._super();
        }
    });
})(jQuery);