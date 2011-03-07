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
            this.element.addClass("icon32-usage-" + o.usage);
            this._status = $.getStatus();
            this._form =  $("<form><input type='text', id='color' value='#123456'/></form>");
            this._picker =  $("<div id='colorpicker' class='colorpicker'></div>");
            this._preview =  $("<div id='preview' class='preview'></div>");
            this.element.append(this._picker);
            this.element.append(this._preview);
            $('#colorpicker').farbtastic('#colorpicker');
            $.farbtastic('#colorpicker').linkTo(function(color, dontCallCmd){self.setColor(color, dontCallCmd)});
            this._initValues(1);
        },

        setColor: function(color, dontCallCmd) {
            var self = this, o = this.options;
            // change preview color
            $('#preview').css({
                backgroundColor: color,
            });
            // call command
            if (dontCallCmd != 1) {
                rest.get(['command', o.devicetechnology, o.deviceaddress, 'setcolor', color],
                    function(data) {
                        var status = (data.status).toLowerCase();
                        if (status != 'ok') {
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
                    $.farbtastic('#colorpicker').setColor(stat.value, 1);
                });
            }
        },
        
        _eventHandler: function(timestamp, value) {
            var self = this, o = this.options;
            $.farbtastic('#colorpicker').setColor(value, 1);
        },

    });
})(jQuery);


