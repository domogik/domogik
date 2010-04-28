const trigger_reset_status = 4000; // 4 seconds

(function($) {
    $.widget("ui.trigger_command", {
        _init: function() {
            var self = this, o = this.options;
            this.element.trigger_command_widget_core({
                usage: o.usage
            })
                .attr("tabindex", 0)
                .click(function () {self.trigger()})
                .keypress(function (e) {if (e.which == 13 || e.which == 32) {self.trigger()}});
        },
        
        trigger: function() {
            this.runAction();
        },
        
        runAction: function(state) {
            var self = this, o = this.options;
            this.element.trigger_command_widget_core('startProcessingState');
            o.action(this);
        },
        
        cancel: function() {
            this.element.trigger_command_widget_core('stopProcessingState');
            this.element.trigger_command_widget_core('displayStatusError');
        },
        
        /* Valid the processing state */
        valid: function(confirmed) {
            var self = this, o = this.options;
            this.element.trigger_command_widget_core('stopProcessingState');
            if (confirmed) {
                this.element.trigger_command_widget_core('displayStatusOk');
                this.element.doTimeout( 'resetStatus', trigger_reset_status, function(){
                    self.element.trigger_command_widget_core('displayResetStatus');
    			});
            }
        }
    });
    
    $.extend($.ui.trigger_command, {
        defaults: {
        }
    });
    
    /* Widget */
    
    $.widget("ui.trigger_command_widget_core", {
        _init: function() {
            var self = this, o = this.options;
            this.element.addClass('widget');
            this.element.addClass('command_trigger');
            this.elementicon = $("<div class='widget_icon icon32-state-" + o.usage + "'></div>");
            this.element.append(this.elementicon);            
            if(o.inactive) {
                this.elementicon.addClass('inactive');         
            } else {
                this.elementstate = $("<div class='widget_state'>---</div>");
                this.elementicon.append(this.elementstate);
                this.element.addClass('command');
                this.elementicon.processing();
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
    
    $.extend($.ui.trigger_command_widget_core, {
        defaults: {
            isCommand: true
        }
    });    
})(jQuery);