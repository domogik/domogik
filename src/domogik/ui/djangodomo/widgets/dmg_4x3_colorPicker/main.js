(function($) {
    $.create_widget({
        // default options
        options: {
            version: 0.1,
            creator: 'Domogik',
            id: 'dmg_4x3_colorPicker',
            name: 'RGB Color Picker',
            description: 'RGB Color Picker to manage colored lights',
            type: 'actuator.string',
            height: 3,
            width: 4,
            displayname: true,
			displayborder: true
        },

        _init: function() {
            var self = this, o = this.options;
            //this.element.addClass("icon32-usage-" + o.usage);
            this._switch = $("<div id='switch' class='switch'></div>");
            this._switch.addClass("icon32-usage-" + o.usage);
            this._switch.addClass('clickable')
            this._switch.click(function (e) {self.action();e.stopPropagation();})
                .keypress(function (e) {if (e.which == 13 || e.which == 32) {self.action; e.stopPropagation();}});                    
            this._status = $.getStatus();
            this._form =  $("<form><input type='text', id='color' value='#123456'/></form>");
            this._picker_off =  $("<div id='colorpicker_off' class='colorpicker_off'></div>");
            this._picker =  $("<div id='colorpicker' class='colorpicker'></div>");
            this._preview =  $("<div id='preview' class='preview'></div>");
            this.element.append(this._switch);
            this.element.append(this._picker_off);
            this.element.append(this._picker);
            this.element.append(this._preview);
            $('#colorpicker').farbtastic('#colorpicker');
            $.farbtastic('#colorpicker').linkTo(function(color, dontCallCmd){self.resetTimerSetColor(color, dontCallCmd)});
            this._initValues(1);
        },

        
        action: function() {
            var self = this, o = this.options;
            currentValue = $('#switch').data('currentValue');
            if (!currentValue) {
                // state unknown
                // Suppose the switch currently off
                currentValue = "off";
            }
            if ((currentValue == "off") || (currentValue == "#000000")) {
                rest.get(['command', o.devicetechnology, o.deviceaddress, 'setcolor', 'on'],
                    function(data) {
                        var status = (data.status).toLowerCase();
                        if (status == 'ok') {
                            $('#colorpicker').show();
                            $('#preview').show();
                            $('#colorpicker_off').hide();
                            self.displayValue('on');
                        } else {
                            /* Error */
                            $.notification('error', data.description);
                        }
                    }
                );
            }
            else {
                rest.get(['command', o.devicetechnology, o.deviceaddress, 'setcolor', 'off'],
                    function(data) {
                        var status = (data.status).toLowerCase();
                        if (status == 'ok') {
                            $('#colorpicker').hide();
                            $('#preview').hide();
                            $('#colorpicker_off').show();
                            self.displayValue('off');
                        } else {
                            /* Error */
                            $.notification('error', data.description);
                        }
                    }
                );
            }
        },

        resetTimerSetColor: function(color, dontCallCmd) {
            var self = this;
            this.element.doTimeout('timeout', 
                                   timer_on_command,
                                   function() {
                                       self.setColor(color, dontCallCmd);
                                   });

        },

        setColor: function(color, dontCallCmd) {
            var self = this, o = this.options;
            // change preview color
            $('#preview').css({
                backgroundColor: color,
            });
            $.farbtastic('#colorpicker').setColor(color);
            // call command
            if (dontCallCmd != 1) {
                rest.get(['command', o.devicetechnology, o.deviceaddress, 'setcolor', color],
                    function(data) {
                        var status = (data.status).toLowerCase();
                        if (status == 'ok') {
                            $('#colorpicker').show();
                            $('#preview').show();
                            $('#colorpicker_off').hide();
                        }
                        else {
                            /* Error */
                            $.notification('error', data.description);
                        }
                    }
                );
            }
        },

        _statsHandler: function(stats) {
            var self = this, o = this.options;
            this.values = [];
            if (stats && stats.length > 0) {
                this.previous = null;
                $.each(stats, function(index, stat){
                    $('#switch').data('currentValue', stat.value);
                    if ((stat.value == "off") || (stat.value == "#000000")){
                        $('#colorpicker').hide();
                        $('#preview').hide();
                        $('#colorpicker_off').show();
                    }
                    else {
                        $('#colorpicker_off').hide();
                        $('#colorpicker').show();
                        $('#preview').show();
                        self.setColor(stat.value, 1);
                    }
                });
            }
        },
        
        _eventHandler: function(timestamp, value) {
            var self = this, o = this.options;
            $('#switch').data('currentValue', value);
            if ((value == "off") || (value == "#000000")) {
                $('#colorpicker').hide();
                $('#preview').hide();
                $('#colorpicker_off').show();
            }
            else {
                $('#colorpicker_off').hide();
                $('#colorpicker').show();
                $('#preview').show();
                self.setColor(value, 1);
            }
        },

        displayValue: function(value) {
            var self = this, o = this.options;
            if (value != null) {
                if (value != "off") {
                    this._switch.displayIcon('value_1');
                } else {
                    this._switch.displayIcon('value_0');
                }
            } 
            else { // Unknown
                this._switch.displayIcon('unknown');   
            }
        },

    });
})(jQuery);


