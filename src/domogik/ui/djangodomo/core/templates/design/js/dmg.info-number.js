(function($) {    
    $.widget("ui.number_info_widget", {
        _init: function() {
            var self = this, o = this.options;
            this.element.addClass('widget');
            this.element.addClass('info_number');
            this.elementicon = $("<div class='widget_icon'></div>");
            this.element.append(this.elementicon);
            if (o.inactive) {
                this.elementicon.attr('class', 'widget_icon icon32-info-' + o.usage + ' inactive');                             
            } else {
                this.setValue(null);                
            }
        },
        
        setValue: function(value) {
            var self = this, o = this.options;
            if (value) {
                this.elementicon.attr('class', 'widget_icon icon32-info-' + o.usage + ' number');             
                this.elementicon.text(value + ' ' + o.unit)
            } else { // Unknown
                this.elementicon.attr('class', 'widget_icon icon32-info-' + o.usage + ' unknown');
                this.elementicon.text('?? ' + o.unit)
            }
        }
    });
    
    $.extend($.ui.number_info_widget, {
        defaults: {
        }
    });    
})(jQuery);