(function($) {
    $.ui.widget_1x1_extended.subclass ('ui.dmg_1x1_basicSensorBoolean', {
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
            // For 1x1 Extended widget
            isOpenable: false,
            hasStatus: true
        },

        widget: function(params) {
            this._super(params);
            var self = this, o = this.options;
            this.setValue(null);
        },

        setValue: function(value, unit, previous) {
            var self = this, o = this.options;
            if (value) {
                value = value.toLowerCase();
                this._displayIcon('boolean');
                if (value == "high") {
                    this._elementValue.attr('class' ,'widget_value icon32-status-active');
                } else { // low
                    this._elementValue.attr('class' ,'widget_value icon32-status-inactive');
                }
                this._elementStatus.html(value);
            } else { // Unknown
                this._displayIcon('unknown');             
                this._elementValue.attr('class' ,'widget_value icon32-status-unknown');
                this._elementStatus.html("--");
            }
            this.previousValue = value;
        }
    });
    register_widget('sensor.boolean', 'dmg_1x1_basicSensorBoolean');
})(jQuery);