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
                .click(1000, function(e){self._panel.show();e.stopPropagation();})
                .click(function(e){self.action();e.stopPropagation();});
            this._panel = $("<div class='panel' width='190' height='190'></div>");
            this._panel.append("<canvas class='deco' width='190' height='190'></canvas>")
            this._panel.append("<div class='value'></div>")
            this._panel.append("<div class='command increase'></div>")
            this._panel.append("<div class='command decrease'></div>")
            this._panel.append("<div class='command close'></div>")
            
            $(".increase", this._panel).click(function(e){self.increase();e.stopPropagation();});
            $(".decrease", this._panel).click(function(e){self.decrease();e.stopPropagation();});
            $(".close", this._panel).click(function(e){self._panel.hide();e.stopPropagation();});
            var value = (o.model_parameters.valueMax - o.model_parameters.valueMin) / 2;

            this.element.append(this._panel);
            $(".value", this._panel).moveToCircleCoord({x:95, y:95, r:65, deg:80});
            $(".command.increase", this._panel).moveToCircleCoord({x:95, y:95, r:70, deg:-20, rotate:true});
            $(".command.decrease", this._panel).moveToCircleCoord({x:95, y:95, r:70, deg:20, rotate:true});
            $(".command.close", this._panel).moveToCircleCoord({x:95, y:95, r:70, deg:150, rotate:true});
            this._panel.hide();
            var canvas = $(".deco", this._panel).get(0);
            if (canvas.getContext) {
                var ctx = canvas.getContext('2d');
                ctx.beginPath();
                ctx.strokeStyle = "#BDCB2F";
                ctx.lineWidth = 2;
                ctx.arc(95,95,94,0,(Math.PI*2),true); // Outer circle  
                ctx.stroke();
                ctx.beginPath();
                ctx.strokeStyle = "#000000";
                ctx.lineWidth = 36;
                ctx.lineCap = 'round';
                ctx.arc(95,95,70,(Math.PI/180)*150,(Math.PI/180)*80,false); // Main circle  
                ctx.stroke();

                var c = getCircleCoord(95, 95, 65, 80);
                ctx.beginPath();
                ctx.strokeStyle = "#000000";
                ctx.fillStyle = "#eeeeee";
                ctx.lineWidth = 5;
                ctx.lineCap = 'butt';
                ctx.arc(c.x,c.y,20,0,(Math.PI*2),true); // Value circle  
                ctx.fill();
                ctx.stroke();
            }
            this.setParameter(value);
        },

        _statsHandler: function(stats) {
        },
        
        _eventHandler: function(date, value) {
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
    			this.value++;
    			this.setParameter(this.value);                
            }
		},
		
		decrease: function() {
            var self = this, o = this.options;
            if (this.value > o.model_parameters.valueMin) {
    			this.value--;
    			this.setParameter(this.value);                
            }
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
        }
    });
})(jQuery);