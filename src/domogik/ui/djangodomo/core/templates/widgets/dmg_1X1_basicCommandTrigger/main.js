(function($) {
    $.ui.widget_1x1_extended.subclass ('ui.dmg_1x1_basicCommandTrigger', {
        // default options
        options: {
            version: 0.1,
            creator: 'Domogik',
            id: 'dmg_1x1_basicCommandTrigger',
            name: 'Basic widget',
            description: 'Basic widget with border and name',
            type: 'actuator.trigger',
            height: 1,
            width: 1,
            // For 1x1 Extended widget
            isOpenable: false,
            hasStatus: false
        },

        widget: function(params) {
            this._super(params);
            var self = this, o = this.options, p = this.params;
            this._displayIcon('unknown');
        },
        
        action: function() {
            var self = this, o = this.options, p = this.params;
            this._startProcessingState();
            $.getREST(['command', p.devicetechnology, p.deviceaddress, p.featurecommand],
                function(data) {
                    var status = (data.status).toLowerCase();
                    if (status == 'ok') {
                        self.valid(p.featureconfirmation);
                    } else {
                        /* Error */
                        self.cancel();
                    }
                }
            );
        }
    });
    register_widget('actuator.trigger', 'dmg_1x1_basicCommandTrigger');
})(jQuery);