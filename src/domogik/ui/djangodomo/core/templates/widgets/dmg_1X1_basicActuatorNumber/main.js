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
            this.element.processing();
            this.element.append("<div class='openpanel'></div>");
            $(".openpanel", this.element).addClass("icon32-usage-" + o.usage)
                .click(function(e){self.onclick();e.stopPropagation();});
            this._panel = $("<div class='dmg_1x1_basicActuatorNumber_commandpanel'><canvas class='deco' width='60' height='100'></canvas><div class='commands'><div class='value'></div><div class='command increase'></div><div class='command decrease'></div></div></div>");
            this.element.before(this._panel);
            this._panel.hide();
            $(".increase", this._panel).click(function(e){self.increase();e.stopPropagation();});
            $(".decrease", this._panel).click(function(e){self.decrease();e.stopPropagation();});
            var value = (o.model_parameters.valueMax - o.model_parameters.valueMin) / 2;
            this._setValue(value);
            
            var canvas = $(".deco", this._panel).get(0);
            if (canvas.getContext) {
                var ctx = canvas.getContext('2d');
                ctx.beginPath();
                ctx.moveTo(60, 95);
                ctx.quadraticCurveTo(-5, 110, 0, 65);
                ctx.quadraticCurveTo(-5, 30, 40, 30);
                ctx.quadraticCurveTo(60, 30, 60, 0);
                ctx.fill();
            }
        },

        _setValue: function(value) {
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
    			this.value++;
                this._resetAutoClose();
    			this._setValue(this.value);                
            }
		},
		
		decrease: function() {
            var self = this, o = this.options;
            if (this.value > o.model_parameters.valueMin) {
    			this.value--;
                this._resetAutoClose();
    			this._setValue(this.value);                
            }
		},
        
        onclick: function() {
            if (this.isOpen) {
                this.action();
            }
            this.switchPanel();
        },
        
        switchPanel: function() {
            var self = this, o = this.options;
            if (this.isOpen) {
                this._panel.hide();
                this.element.doTimeout( 'timeout');
                this.element.removeClass('opened');
            } else {
                this._panel.show();
//                this.element.doTimeout( 'timeout', close_without_change, function(){
//                    self.switchPanel();
//                });
                this.element.addClass('opened');
            }
            this.isOpen = !this.isOpen;
        },
        
        action: function() {
            var self = this, o = this.options;
            self._startProcessingState();
            $.getREST(['command', o.devicetechnology, o.deviceaddress, o.model_parameters.command, self.value],
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
        },
        
        _resetAutoClose: function() {
			var self = this;
			this.element.doTimeout( 'timeout', close_with_change, function(){
                self.action();
                self.switchPanel();
			});	
		}
    });
})(jQuery);
