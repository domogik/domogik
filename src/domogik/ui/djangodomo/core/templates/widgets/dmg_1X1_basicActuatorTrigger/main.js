(function($) {
    $.create_widget({
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
            displayname: true,
			displayborder: true
        },

        _init: function() {
            var self = this, o = this.options;
            this.element.addClass("icon32-usage-" + o.usage)
                .addClass('clickable')
                .processing();
            this._status = $.getStatus();
            this.element.append(this._status);
            this.element.displayIcon('unknown');
            this.element.click(function (e) {self.action();e.stopPropagation();})
                .keypress(function (e) {if (e.which == 13 || e.which == 32) {self.action; e.stopPropagation();}});                    
        },
        
        _statsHandler: function(stats) {
        },

        _eventHandler: function(date, value) {
        },

        action: function() {
            var self = this, o = this.options;
            this.element.startProcessingState();
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
        },
        
        cancel: function() {
            var self = this, o = this.options;
            this.element.stopProcessingState();
            this._status.displayStatusError();
        },

        /* Valid the processing state */
        valid: function(confirmed) {
            var self = this, o = this.options;
            this.element.stopProcessingState();
            if (confirmed) {
                this._status.displayStatusOk();
                this.element.doTimeout( 'resetStatus', state_reset_status, function(){
                    self._status.displayResetStatus();
                });
            } else {
                self._status.displayResetStatus();                
            }
        }
    });
})(jQuery);