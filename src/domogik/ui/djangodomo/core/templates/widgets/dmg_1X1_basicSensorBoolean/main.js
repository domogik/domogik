(function($) {
    $.create_widget({
        // default options
        options: {
            version: 0.1,
            creator: 'Domogik',
            id: 'dmg_1x1_basicSensorBoolean',
            name: 'Basic widget',
            description: 'Basic widget with border and name',
            type: 'sensor.boolean',
            height: 1,
            width: 1,
            displayname: true,
			displayborder: true
        },

        _init: function() {
            var self = this, o = this.options;
            this.element.addClass("icon32-usage-" + o.usage)

            this._value =  $("<div class='value'></div>");
            this.element.append(this._value);

            this._status = $.getStatus();
            this.element.append(this._status);

            this._initValues(1);
        },

        _statsHandler: function(stats) {
            if (stats && stats.length > 0) {
                this.setValue(stats[0].value);
            } else {
                this.setValue(null);
            }
        },
        
        _eventHandler: function(date, value) {
            this.setValue(value);
        },

        setValue: function(value, unit, previous) {
            var self = this, o = this.options;
            if (value) {
                this.element.displayIcon('known');             
                value = value.toLowerCase();
                if (value == "high") {
                    this._value.attr('class' ,'value icon32-status-active');
                } else { // low
                    this._value.attr('class' ,'value icon32-status-inactive');
                }
                this._status.html(value);
            } else { // Unknown
                this.element.displayIcon('unknown');             
                this._value.attr('class' ,'value icon32-status-unknown');
                this._status.html("--");
            }
            this.previousValue = value;
        }
    });
})(jQuery);