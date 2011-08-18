(function($) {
    $.create_widget({
        // default options
        options: {
            version: 0.1,
            creator: 'Domogik',
            id: 'dmg_1x1_basicActuatorNumber',
            name: 'Basic widget',
            description: 'Basic widget with hidden/show command',
            type: 'actuator.number',
            height: 1,
            width: 1,
            displayname: true,
			displayborder: true
        },

        _init: function() {
            var self = this, o = this.options;
            this.isOpen = false;
            this.element.addClass("icon32-usage-" + o.usage)
                .processing();
            this.element.append("<div class='openpanel'></div>");
            $(".openpanel", this.element).click(1000, function(e){self._panel.show();e.stopPropagation();})
                .click(function(e){self.action();e.stopPropagation();});
                
            this._panel = $.getPanel({width:190, height:190, circle: {start:150, end:80}});
            this.element.append(this._panel);
            this._panel.panelAddCommand({label:'Increase', showlabel: false, className:'increase', r:70, deg:-20, rotate:true, click:function(e){self.increase();e.stopPropagation();}});
            this._panel.panelAddCommand({label:'Decrease', showlabel: false, className:'decrease', r:70, deg:20, rotate:true, click:function(e){self.decrease();e.stopPropagation();}});
            this._panel.panelAddCommand({label:'Close', showlabel: false, className:'close', r:70, deg:150, rotate:true, click:function(e){self._panel.hide();e.stopPropagation();}});
            this._panel.panelAddText({className:'value', r:65, deg:80});
            this._panel.hide();

            var value = Math.round((o.model_parameters.valueMax - o.model_parameters.valueMin) / 2);
            this.setParameter(value);
        },

        _statsHandler: function(stats) {
        },
        
        _eventHandler: function(timestamp, value) {
        },
        
        setParameter: function(value) {
            var self = this, o = this.options;
            if (value != null) {
                this.value = value;
                $(".value", this._panel).text(value);
                if (value == o.model_parameters.valueMax) {
                    $(".increase", this._panel).hide();
                } else if (value == o.model_parameters.valueMin) {
                    $(".decrease", this._panel).hide();                    
                } else {
                    $(".increase", this._panel).show();
                    $(".decrease", this._panel).show();                                        
                }
            }
        },
        
        increase: function() {
            var self = this, o = this.options;
            if (this.value < o.model_parameters.valueMax) {
    			Math.round(this.value++);
    			this.setParameter(this.value);                
            }
		},
		
		decrease: function() {
            var self = this, o = this.options;
            if (this.value > o.model_parameters.valueMin) {
    			Math.round(this.value--);
    			this.setParameter(this.value);                
            }
		},

        action: function() {
            var self = this, o = this.options;
            self._startProcessingState();
            rest.get(['command', o.devicetechnology, o.deviceaddress, o.model_parameters.command, self.value],
                function(data) {
                    self._stopProcessingState();
                    var status = (data.status).toLowerCase();
                    if (status == 'ok') {
                    } else {
                        $.notification('error', data.description);
                    }
                }
            );
        },
        
        _startProcessingState: function() {
            this.element.processing('start');
        },

        _stopProcessingState: function() {
            this.element.processing('stop');
        }
    });
})(jQuery);