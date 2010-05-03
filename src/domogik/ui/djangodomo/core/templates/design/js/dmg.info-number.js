(function($) {    
    $.widget("ui.number_info_widget", {
        _init: function() {
            var self = this, o = this.options;
            this.element.addClass('widget');
            this.element.addClass('info_number');
            this.elementicon = $("<div class='widget_icon'></div>");
            this.element.append(this.elementicon)
                .attr("tabindex", 0)
                .click(function () {self.showGraph()})
                .keypress(function (e) {if (e.which == 13 || e.which == 32) {self.showGraph()}});

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
        },
        
        showGraph: function() {
            var self = this, o = this.options;
            $.getREST(['stats', o.deviceid, o.key, 'from', '20100401'],
                function(data) {
                    var status = (data.status).toLowerCase();
                    if (status == 'ok') {
                        var d = [];
                        var c = 1;
                        for each (var stat in data.stats) {
                            d.push([c, parseInt(stat.value,10)]);
                            c++;
                        }                        
                        var dialog = $("<div id='dialog' title='Graph Test'><div id='graph' style='width:600px;height:300px;'></div></div>");
                        $('body').append(dialog);
                        dialog.dialog({ height: 340, width:640, resizable: false });
                        
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
})(jQuery);