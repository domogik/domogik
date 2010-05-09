(function($) {    
    $.ui.widget_mini_core.subclass ('ui.widget_mini_command_binary', {
        // default options
        options: {
            widgettype: 'command_binary',
            nameposition: 'top'
        },

        _init: function() {
            var self = this, o = this.options;
            this.values = [o.value0, o.value1];
            this.texts = [o.text0, o.text1];

            this.element.click(function (e) {self._onclick();e.stopPropagation();})
                .keypress(function (e) {if (e.which == 13 || e.which == 32) {self._onclick()}});
            this.setValue(null);
        },
        
        _onclick: function() {
            if (this.isOpen) {
                this.close();
                this.switchState()
            } else {
                this.open();
            }
        },
        
        setValue: function(value) {
            if (value) {
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
            if (value) {
                if (value == 1) {
                    this._displayIcon('binary_1');             
                } else {
                    this._displayIcon('binary_0');             
                }
                this._writeStatus(o.texts[value]);
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
            this.setvalue(this.processingValue);
        },

        switchState: function() {
            if (this.currentValue) {
                this.processingValue = (this.currentValue == 0)?1:0;                
            } else { // Current state unknown
                // Suppose the switch currently off
                this.processingValue = 1;
            }
            this.runAction({value : this.values[this.processingValue]});
        }
    });
})(jQuery);