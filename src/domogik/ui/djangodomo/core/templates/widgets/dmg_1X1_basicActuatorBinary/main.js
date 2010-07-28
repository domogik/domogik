(function($) {
    $.ui.widget_1x1_extended.subclass ('ui.dmg_1x1_basicActuatorBinary', {
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

        widget: function(params) {
            this._super(params);
            var self = this, o = this.options, p = this.params;
            this.values = [p.model_parameters.value0, p.model_parameters.value1];
            this.texts = [p.usage_parameters.state0, p.usage_parameters.state1];
            this.setValue(null);            
        },
        
        action: function() {
            var self = this, o = this.options, p = this.params;
            this._startProcessingState();
            if (this.currentValue) {
                this.processingValue = (this.currentValue == 0)?1:0;                
            } else { // Current state unknown
                // Suppose the switch currently off
                this.processingValue = 1;
            }
            $.getREST(['command', p.devicetechnology, p.deviceaddress, this.values[this.processingValue]],
                function(data) {
                    var status = (data.status).toLowerCase();
                    if (status == 'ok') {
                        self.valid(p.featureconfirmation);
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
    register_widget('actuator.binary', 'dmg_1x1_basicActuatorBinary');
})(jQuery);