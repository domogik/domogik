(function($) {
    $.create_widget_1x1_extended({
        // default options
        options: {
            version: 0.1,
            creator: 'Domogik',
            id: 'dmg_1x1_basicActuatorTrigger',
            name: 'Basic widget',
            description: 'Basic widget with border and name',
            type: 'actuator.trigger',
            height: 1,
            width: 1,
            // For 1x1 Extended widget
            isOpenable: false,
            hasStatus: false
        },

        _init: function() {
            var self = this, o = this.options;
            this._displayIcon('unknown');
        },
        
        action: function() {
            var self = this, o = this.options;
            this._startProcessingState();
            $.getREST(['command', o.devicetechnology, o.deviceaddress, o.model_parameters.command],
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
        }
    });
})(jQuery);