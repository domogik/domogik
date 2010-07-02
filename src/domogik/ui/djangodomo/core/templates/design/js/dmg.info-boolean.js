(function($) {    
    $.ui.widget_mini_core.subclass ('ui.widget_mini_info_boolean', {
        // default options
        options: {
            widgettype: 'info_boolean',
            nameposition: 'nametop'
        },

        _init: function() {
            var self = this, o = this.options;
            this.element.click(function (e) {self._onclick();e.stopPropagation();})
                .keypress(function (e) {if (e.which == 13 || e.which == 32) {self._onclick()}});
            this._elementValue =  $("<div class='widget_value'></div>");
            this.element.append(this._elementValue);
            
            this.setValue(null);                
        },
        
        _onclick: function() {
            if (this.isOpen) {
                this.close();
            } else {
                this.open();
            }
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
})(jQuery);