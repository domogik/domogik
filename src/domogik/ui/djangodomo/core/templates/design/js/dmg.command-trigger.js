(function($) {    
    $.ui.widget_mini_core.subclass ('ui.widget_mini_command_trigger', {
        // default options
        options: {
            widgettype: 'command_trigger',
            nameposition: 'top'
        },

        _init: function() {
            var self = this, o = this.options;
            this.element.click(function (e) {self._onclick();e.stopPropagation();})
                .keypress(function (e) {if (e.which == 13 || e.which == 32) {self._onclick()}});
            this._displayIcon('unknown');
        },
        
        _onclick: function() {
            if (this.isOpen) {
                this.close();
                this.trigger();
            } else {
                this.open();
            }
        },
        
        trigger: function() {
            this.runAction(null);
        }
    });
})(jQuery);