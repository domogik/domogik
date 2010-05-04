(function($) {    
    $.widget("ui.number_info_widget", {
        _init: function() {
            var self = this, o = this.options;
            this.element.number_info_widget_core({
                usage: o.usage
            })
                .attr("tabindex", 0)
                .click(function () {self.showGraph()})
                .keypress(function (e) {if (e.which == 13 || e.which == 32) {self.showGraph()}});
            

        },
        
        setValue: function(value) {
            var self = this, o = this.options;
            this.element.number_info_widget_core('setValue', value, o.unit);
        },
        
        showGraph: function() {
            var self = this, o = this.options;
            $.getREST(['stats', o.deviceid, o.key, 'from', '20100401'],
                function(data) {
                    var status = (data.status).toLowerCase();
                    if (status == 'ok') {
                        var d = [];
                        $.each(data.stats, function(index, stat) {
                            d.push([index, stat.value]);
                        });
                        var dialog = $("<div id='dialog' title='Graph Test'><div id='graph' style='width:600px;height:300px;'></div></div>");
                        $('body').append(dialog);
                        dialog.dialog({ height: 340, width:640,
                                        resizable: false,
                                        close: function(ev, ui) {
                                            $(this).remove();
                                        }
                                    });
                        
                        $.plot($("#graph"), [d], {
                             /* xaxis: {
                                mode: "time",
                                timeformat: "%y/%m/%d"
                              }*/
                        });
                    } else {
                        $.notification('error', '{% trans "data creation failed" %} (' + data.description + ')');                                                                      
                    }
                }
            );
        }
    });
    
    $.extend($.ui.number_info_widget, {
        defaults: {
        }
    });
    
    $.widget("ui.number_info_widget_core", {
        _init: function() {
            var self = this, o = this.options;
            this.element.addClass('widget');
            this.element.addClass('info_number');
            this.elementicon = $("<div class='widget_icon'></div>");
            this.elementvalue =  $("<div class='widget_value'></div>");
            this.elementicon.append(this.elementvalue);
            this.element.append(this.elementicon);
            if (o.inactive) {
                this.elementicon.attr('class', 'widget_icon icon32-info-' + o.usage + ' inactive');                             
            } else {
                this.setValue(null);                
            }
        },
        
        setValue: function(value, unit) {
            var self = this, o = this.options;
            if (value) {
                this.elementicon.attr('class', 'widget_icon icon32-info-' + o.usage + ' number');             
                this.elementvalue.html(value + '<br />' + unit)
            } else { // Unknown
                this.elementicon.attr('class', 'widget_icon icon32-info-' + o.usage + ' unknown');
                this.elementvalue.html('--<br />' + unit)
            }
        }
    });
    
    $.extend($.ui.number_info_widget_core, {
        defaults: {
        }
    });    
})(jQuery);