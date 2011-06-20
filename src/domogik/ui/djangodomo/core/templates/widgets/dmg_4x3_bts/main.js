(function($) {
    $.create_widget({
        // default options
        options: {
            version: 0.1,
            creator: 'Domogik',
            id: 'dmg_4x3_bts',
            name: 'BTS',
            description: 'BTS',
            type: 'actuator.trigger',
            height: 3,
            width: 4,
            displayname: true,
			displayborder: true
        },

        _init: function() {
            var self = this, o = this.options;
            this.element.addClass("icon32-usage-" + o.usage)
                .processing();
            var button1 = $("<button id='button1' class='button'>A</button>");
            button1.click(function (e) {self.action1();e.stopPropagation();})
                .keypress(function (e) {if (e.which == 13 || e.which == 32) {self.action1; e.stopPropagation();}});
            this.element.append(button1);

            var button2 = $("<button id='button2' class='button'>B</button>");
            button2.click(function (e) {self.action2();e.stopPropagation();})
                .keypress(function (e) {if (e.which == 13 || e.which == 32) {self.action2; e.stopPropagation();}});
            this.element.append(button2);

            var button3 = $("<button id='button3' class='button'>C</button>");
            button1.click(function (e) {self.action3();e.stopPropagation();})
                .keypress(function (e) {if (e.which == 13 || e.which == 32) {self.action3; e.stopPropagation();}});
            this.element.append(button3);

        },
        
        _statsHandler: function(stats) {
        },

        _eventHandler: function(date, value) {
        },

        action1: function() {
            var self = this, o = this.options;
            this.element.startProcessingState();
            rest.get(['command', o.devicetechnology, o.deviceaddress, o.model_parameters.command],
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

        action2: function() {
            var self = this, o = this.options;
            this.element.startProcessingState();
            rest.get(['command', o.devicetechnology, o.deviceaddress, o.model_parameters.command],
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
        
        action3: function() {
            var self = this, o = this.options;
            this.element.startProcessingState();
            rest.get(['command', o.devicetechnology, o.deviceaddress, o.model_parameters.command],
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