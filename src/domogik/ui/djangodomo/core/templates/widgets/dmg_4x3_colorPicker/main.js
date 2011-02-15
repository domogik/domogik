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
            $.farbtastic('#colorpicker').linkTo(self.setColor);
            this._initValues(1);
        },

        setColor: function(color) {
            var self = this, o = this.options;
            // TODO : pourquoi ça marche pas la récup de o ????
            // change preview color
            $('#preview').css({
                backgroundColor: color,
            });
            // call command
            rest.get(['command', o.devicetechnology, o.deviceaddress, color],
                function(data) {
                    var status = (data.status).toLowerCase();
                    if (status != 'ok') {
                        /* Error */
                        $.notification('error', data.description);
                    }
                }
            );
        },

        _statsHandler: function(stats) {
            var self = this, o = this.options;
            this.values = [];
            if (stats && stats.length > 0) {
                this.previous = null;
                $.each(stats, function(index, stat){
                    alert(stat);
                });
            }
        },
        
        _eventHandler: function(timestamp, value) {
            var self = this, o = this.options;
        },

    });
})(jQuery);


