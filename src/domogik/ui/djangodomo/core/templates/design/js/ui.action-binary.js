(function($) {
    
    $.widget("ui.binary_command", {
        _init: function() {
            var self = this, o = this.options;
            this.states = o.states.toLowerCase().split(/\s*,\s*/);
            this.widgets = new Array();
            this.element.addClass('command_binary')
                .addClass('icon32-state-' + o.usage);
            var ul = $("<ul></ul>");
            var li0 = $("<li></li>");
            var a0 = $("<button class='buttontext capitalletter'>" + this.states[0] + "</button>");
            a0.click(function() {
                    self.runAction(0);
                });
            var li1 = $("<li></li>");
            var a1 = $("<button class='buttontext capitalletter'>" + this.states[1] + "</button>");
            a1.click(function() {
                    self.runAction(1);
                });
            li0.append(a0);
            li1.append(a1);
            ul.append(li0);
            ul.append(li1);
            this.element.append(ul);
        },
        
        setState: function(state) {
            var self = this;
            if (state == 1 || state.toLowerCase() == this.states[1]) {
                this.currentState = 1;
            } else {
                this.currentState = 0;
            }
            this.displayState(this.currentState);
            $.each(this.widgets, function(index, value) {
                $(value).binary_widget('setState', self.currentState);
            });
        },
        
        displayState: function(state) {
            if (state == 1) {
                this.element.addClass('binary_1');                
                this.element.removeClass('binary_0');                                
            } else {
                this.element.addClass('binary_0');                                
                this.element.removeClass('binary_1');                                
            }
        },
        
        switchState: function() {
            var switchState = (this.currentState == 0)?1:0;
            this.runAction(switchState);
        },
        
        runAction: function(state) {
            this.options.action(this, this.states[state]);
        },
        
        registerWidget: function(id) {
            this.widgets.push(id);
            $(id).binary_widget({
                command: this,
                usage: this.options.usage,
                states: this.states
            })
            .binary_widget('setState', this.currentState);
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
            this.element.addClass('widget_binary')
                .attr("tabindex", 0);
            this.elementstate = $("<div class='widget_state'></div>");
            this.elementicon = $("<div class='widget_icon'></div>");
            this.elementicon.addClass('icon32-state-' + o.usage);
            this.element.append(this.elementstate);
            this.element.append(this.elementicon);
            
        },
        
        displayState: function(state) {
            if (state == 1) {
                this.elementicon.addClass('binary_1');                
                this.elementicon.removeClass('binary_0');
            } else {
                this.elementicon.addClass('binary_0');                                
                this.elementicon.removeClass('binary_1');                                
            }
            this.elementstate.text(this.options.states[state]);
        }
    });
    
    $.extend($.ui.binary_widget_core, {
        defaults: {
        }
    });
    
    $.widget("ui.binary_widget", {
        _init: function() {
            var self = this, o = this.options;
            this.element.binary_widget_core({
                usage: o.usage,
                states: o.states
            })
                .click(function () {self.switchState()})
                .keypress(function (e) {if (e.which == 13 || e.which == 32) {self.switchState()}});
        },
        
        switchState: function() {
            this.options.command.switchState();
        },
        
        setState: function(state) {
            if (state == 1) {
                this.element.binary_widget_core('displayState', 1);
            } else {
                this.element.binary_widget_core('displayState', 0);                
            }
        }
    });
    $.extend($.ui.binary_widget, {
        defaults: {
        }
    });
    
})(jQuery);

/*
function process_binary(function_id, force) {
    $('#widgetmini_' + function_id).addClass('processing_state');
    $('#widget_' + function_id).addClass('processing_state');
    var status = (force == null) ? 1 : force; 
    setTimeout("feedback_binary(" + function_id + ", " + status + ")",3000);
}

function feedback_binary(function_id, status) {
    var widgetmini_id = 'widgetmini_' + function_id;
    var widget_id = 'widget_' + function_id;
    var oldstatus = (status == 0) ? 1 : 0 ;
    $('#' + widgetmini_id).removeClass('processing_state')
        .addClass('ok_state')
        .removeClass('binary_' + oldstatus)
        .addClass('binary_' + status);
    $('#' + widget_id).removeClass('processing_state')
        .addClass('ok_state')
        .removeClass('binary_' + oldstatus)
        .addClass('binary_' + status);
}
*/