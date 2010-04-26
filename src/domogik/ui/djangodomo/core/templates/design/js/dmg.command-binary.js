const binary_reset_status = 4000; // 4 seconds

(function($) {
    $.widget("ui.binary_command", {
        _init: function() {
            var self = this, o = this.options;
            this.values = [o.value0, o.value1];
            this.texts = [o.text0, o.text1];
            this.element.binary_widget_core({
                usage: o.usage,
                texts: this.texts,
                isCommand: true
            })
                .attr("tabindex", 0)
                .click(function () {self.switchState()})
                .keypress(function (e) {if (e.which == 13 || e.which == 32) {self.switchState()}});

        },
        
        setState: function(state) {
            if (state == 1 || state.toLowerCase() == this.values[1]) {
                this.currentState = 1;
            } else {
                this.currentState = 0;
            }
            this.processingState = null;
            this.displayState(this.currentState);
        },
        
        displayState: function(state) {
            if (state == 1) {
                this.element.binary_widget_core('displayState', 1);
            } else {
                this.element.binary_widget_core('displayState', 0);                
            }
        },
                
        switchState: function() {
            this.processingState = (this.currentState == 0)?1:0;
            this.runAction(this.processingState);
        },
        
        runAction: function(state) {
            var self = this, o = this.options;
            this.element.binary_widget_core('startProcessingState');
            o.action(this, this.values[state]);
        },
        
        cancel: function() {
            this.processingState = null;
            this.element.binary_widget_core('stopProcessingState');
            this.element.binary_widget_core('displayStatusError');
        },
        
        /* Valid the processing state */
        valid: function(confirmed) {
            var self = this, o = this.options;
            this.element.binary_widget_core('stopProcessingState');
            if (confirmed) {
                this.element.binary_widget_core('displayStatusOk');
                this.element.doTimeout( 'resetStatus', binary_reset_status, function(){
                    self.element.binary_widget_core('displayResetStatus');
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
    
    $.widget("ui.binary_widget_core", {
        _init: function() {
            var self = this, o = this.options;
            this.element.addClass('widget_binary');
            this.elementicon = $("<div class='widget_icon'></div>");
            this.elementicon.addClass('icon32-state-' + o.usage);                
            this.element.append(this.elementicon);            
            if(o.isCommand) {
                this.elementstate = $("<div class='widget_state'></div>");
                this.elementicon.append(this.elementstate);
                this.element.addClass('command');
                this.elementicon.processing();
            } else {
                this.elementicon.addClass('binary_1');                
            }
        },
        
        displayState: function(state) {
            var self = this, o = this.options;
            if (state == 1) {
                this.elementicon.addClass('binary_1');                
                this.elementicon.removeClass('binary_0');
            } else {
                this.elementicon.addClass('binary_0');                                
                this.elementicon.removeClass('binary_1');                                
            }
            this.elementstate.text(o.texts[state]);
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
    
    $.extend($.ui.binary_widget_core, {
        defaults: {
            isCommand: true
        }
    });    
})(jQuery);