const binary_reset_status = 4000; // 4 seconds

(function($) {
    $.widget("ui.binary_command", {
        _init: function() {
            var self = this, o = this.options;
            this.values = [o.value0, o.value1];
            this.texts = [o.text0, o.text1];
            this.element.binary_command_widget_core({
                usage: o.usage,
                texts: this.texts
            })
                .attr("tabindex", 0)
                .click(function () {self.switchState()})
                .keypress(function (e) {if (e.which == 13 || e.which == 32) {self.switchState()}});
            this.setValue(null);
        },
        
        setValue: function(value) {
            if (value) {
                if (value == 1 || value.toLowerCase() == this.values[1]) {
                    this.currentState = 1;
                } else {
                    this.currentState = 0;
                }                
            } else { // Unknown
                this.currentState = null;
            }
            this.processingState = null;
            this.displayValue(this.currentState);
        },
        
        displayValue: function(value) {
            this.element.binary_command_widget_core('displayValue', value);                
        },
                
        switchState: function() {
            if (this.currentState) {
                this.processingState = (this.currentState == 0)?1:0;                
            } else { // Current state unknown
                this.processingState = 0;
            }
            this.runAction(this.processingState);
        },
        
        runAction: function(state) {
            var self = this, o = this.options;
            this.element.binary_command_widget_core('startProcessingState');
            o.action(this, this.values[state]);
        },
        
        cancel: function() {
            this.processingState = null;
            this.element.binary_command_widget_core('stopProcessingState');
            this.element.binary_command_widget_core('displayStatusError');
        },
        
        /* Valid the processing state */
        valid: function(confirmed) {
            var self = this, o = this.options;
            this.element.binary_command_widget_core('stopProcessingState');
            if (confirmed) {
                this.element.binary_command_widget_core('displayStatusOk');
                this.element.doTimeout( 'resetStatus', binary_reset_status, function(){
                    self.element.binary_command_widget_core('displayResetStatus');
    			});
            }
            setState(this.processingState);
        }
    });
    
    $.extend($.ui.binary_command, {
        defaults: {
        }
    });
    
    /* Widget */
    
    $.widget("ui.binary_command_widget_core", {
        _init: function() {
            var self = this, o = this.options;
            this.element.addClass('widget');
            this.element.addClass('command_binary');
            this.elementicon = $("<div class='widget_icon icon32-state-" + o.usage + "'></div>");
            this.element.append(this.elementicon);            
            if(o.inactive) {
                this.elementicon.addClass('inactive');                
            } else {
                this.elementstate = $("<div class='widget_state'></div>");
                this.elementicon.append(this.elementstate);
                this.element.addClass('command');
                this.elementicon.processing();
            }
        },
        
        displayValue: function(value) {
            var self = this, o = this.options;
            if (value) {
                if (value == 1) {
                    this.elementicon.attr('class', 'widget_icon icon32-state-' + o.usage + ' binary_1');             
                } else {
                    this.elementicon.attr('class', 'widget_icon icon32-state-' + o.usage + ' binary_0');                
                }
                this.elementstate.text(o.texts[value]);
            } else { // Unknown
                this.elementicon.attr('class', 'widget_icon icon32-state-' + o.usage + ' unknown');                             
                this.elementstate.text('---');
            }
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
    
    $.extend($.ui.binary_command_widget_core, {
        defaults: {
            isCommand: true
        }
    });    
})(jQuery);