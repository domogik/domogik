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
            this._value =  $("<div class='value'></div>");
            this.element.append(this._value);

            this.element.addClass("icon32-usage-" + o.usage)
                .addClass('clickable')
                .processing();
            this._status = $.getStatus();
            this.element.append(this._status);
            this.element.click(function (e) {self.action();e.stopPropagation();})
                .keypress(function (e) {if (e.which == 13 || e.which == 32) {self.action; e.stopPropagation();}});
            this.sequence = null;
            if (o.model_parameters.values) {
                $.each(map, function(key, value) {
                    this.sequence.push({'key':key, 'value':value});
                });
            }
            this.sequenceIndex = 0;
        },
        
        _statsHandler: function(stats) {
        },

        _eventHandler: function(date, value) {
        },

        action: function() {
            var self = this, o = this.options;
            var restcommand = null;
            this.element.startProcessingState();
            if (this.sequence) {
                restcommand = ['command', o.devicetechnology, o.deviceaddress, o.model_parameters.command, this.sequence[this.sequenceIndex]['value']]
            } else {
                restcommand = ['command', o.devicetechnology, o.deviceaddress, o.model_parameters.command];
            }
            rest.get(restcommand,
                function(data) {
                    var status = (data.status).toLowerCase();
                    if (status == 'ok') {
                        if (self.sequence) {
                            self._value.html(self.sequence[self.sequenceIndex]['key']);
                            if (self.sequenceIndex == self.sequence.length - 1) {
                                self.sequenceIndex = 0;
                            } else {
                                self.sequenceIndex++;
                            }
                        }
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