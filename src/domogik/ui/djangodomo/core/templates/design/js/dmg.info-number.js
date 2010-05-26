(function($) {    
    $.ui.widget_mini_core.subclass ('ui.widget_mini_info_number', {
        // default options
        options: {
            widgettype: 'info_number',
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
                this._showGraph();
            } else {
                this.open();
            }
        },

        setValue: function(value, unit, previous) {
            var self = this, o = this.options;
            if (value) {
                this._displayIcon('number');             
                this._elementValue.html(value + '<br />' + o.unit)
                if (this.previousValue) {
                    if (value == this.previousValue) {
                        this._elementStatus.attr('class', 'status icon8-status-equal')
                        this._elementStatus.html("<span class='offscreen'>linear</span>");
                    } else if (value > this.previousValue) {
                        this._elementStatus.attr('class', 'status icon8-status-up')
                        this._elementStatus.html("<span class='offscreen'>going up</span>");
                    } else {
                        this._elementStatus.attr('class', 'status icon8-status-down')
                        this._elementStatus.html("<span class='offscreen'>going down</span>");
                    }
                }
            } else { // Unknown
                this._displayIcon('unknown');             
                this._elementValue.html('--<br />' + o.unit)
            }
            this.previousValue = value;
        },

        _showGraph: function() {
            var self = this, o = this.options;
            $.getREST(['stats', o.deviceid, o.key, 'from', '20100401'],
                function(data) {
                    var status = (data.status).toLowerCase();
                    if (status == 'ok') {
                        var d = [];
                        $.each(data.stats, function(index, stat) {
                            d.push([stat.date, stat.value]);
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
                              xaxis: {
                                mode: "time",
                                timeformat: "%y/%m/%d"
                              }
                        });
                    } else {
                        $.notification('error', '{% trans "data creation failed" %} (' + data.description + ')');                                                                      
                    }
                }
            );
        }
    });  
})(jQuery);