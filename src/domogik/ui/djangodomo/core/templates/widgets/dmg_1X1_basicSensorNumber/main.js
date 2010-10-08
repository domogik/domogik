(function($) {
    $.create_widget({
        // default options
        options: {
            version: 0.1,
            creator: 'Domogik',
            id: 'dmg_1x1_basicSensorNumber',
            name: 'Basic widget',
            description: 'Basic widget with border and name',
            type: 'sensor.number',
            height: 1,
            width: 1,
            displayname: true,
			displayborder: true
        },

        _init: function() {
            var self = this, o = this.options;
            this.element.addClass("icon32-usage-" + o.usage)
                .addClass('clickable');
            this._value =  $("<div class='value'></div>");
            this.element.append(this._value);

            this._status = $.getStatus();
            this.element.append(this._status);
            
            this._panel = $.getPanel({width:190, height:190, circle: {start:140, end:90}});
            this.element.append(this._panel);
            this._panel.panelAddCommand({label:'Close', showlabel: false, class:'close', r:70, deg:140, rotate:false, click:function(e){self.close();e.stopPropagation();}});
            this._panel.panelAddCommand({label:'Today', showlabel: true, class:'graph', r:70, deg:50, rotate:false, click:function(e){self.show_graph('day');e.stopPropagation();}});
            this._panel.panelAddCommand({label:'Week', showlabel: true, class:'graph', r:70, deg:10, rotate:false, click:function(e){self.show_graph('week');e.stopPropagation();}});
            this._panel.panelAddCommand({label:'Month', showlabel: true, class:'graph', r:70, deg:-30, rotate:false, click:function(e){self.show_graph('month');e.stopPropagation();}});
            this._panel.panelAddCommand({label:'Year', showlabel: true, class:'graph', r:70, deg:-70, rotate:false, click:function(e){self.show_graph('year');e.stopPropagation();}});
            this._panel.hide();
            
            this.element.click(function (e) {self._onclick();e.stopPropagation();})
                .keypress(function (e) {if (e.which == 13 || e.which == 32) {self._onclick(); e.stopPropagation();}
                          else if (e.keyCode == 27) {self.close(); e.stopPropagation();}});
                
            this._initValues(1);
        },

        _statsHandler: function(stats) {
            if (stats && stats.length > 0) {
                this.setValue(stats[0].value);
            } else {
                this.setValue(null);
            }
        },
        
        _eventHandler: function(timestamp, value) {
            this.setValue(value);
        },

        setValue: function(value) {
            var self = this, o = this.options;
            if (value) {
                this.element.displayIcon('known');             
                this._value.html(value + '<br />' + o.model_parameters.unit)
                if (this.previousValue) {
                    if (value == this.previousValue) {
                        this._status.attr('class', 'widget_status icon8-status-equal')
                        this._status.html("<span class='offscreen'>linear</span>");
                    } else if (value > this.previousValue) {
                        this._status.attr('class', 'widget_status icon8-status-up')
                        this._status.html("<span class='offscreen'>going up</span>");
                    } else {
                        this._status.attr('class', 'widget_status icon8-status-down')
                        this._status.html("<span class='offscreen'>going down</span>");
                    }
                }
            } else { // Unknown
                this.element.displayIcon('unknown');             
                this._value.html('--<br />' + o.model_parameters.unit)
            }
            this.previousValue = value;
        },

        _onclick: function() {
            var self = this, o = this.options;
            if (this.isOpen) {
                this.close();
            } else {
                this.open();
            }
        },

        open: function() {
            if (!this.isOpen) {
                this.isOpen = true;
                this._panel.show();  
                this.element.doTimeout( 'timeout', close_without_change, function(){
                    self.close();
                });
            }
        },

        close: function() {
            if (this.isOpen) {
                this.isOpen = false;
                this._panel.hide();           
            }
            this.element.doTimeout( 'timeout');
        },

        show_graph: function(type) {
            var self = this, o = this.options;
            this.close();
            var dialog = $("<div id='dialog' title='Graph " + type + "'><div id='graph' style='width:100%;height:100%;'></div></div>");
            $('body').append(dialog);
            dialog.dialog({ height: 330, width:630,
                            resizable: false,
                            modal: true,
                            close: function(ev, ui) {
                                $(this).remove();
                            }
                        });

            var now = new Date();
            
            var graph_options = {
                chart: {
                   renderTo: 'graph',
                   defaultSeriesType: 'spline',
                   borderRadius: null,
                   backgroundColor:'#eeeeee'
                },
                credits:{
                    enabled : false
                },
                title: {
                   text: null
                },
                xAxis: {
                    min: null,
                    max: null,
                    type: 'datetime'
                },
                yAxis: {
                   title: {
                      text: o.featurename + ' (' + o.model_parameters.unit + ')'
                   }
                },
                legend: {
                    enabled: false
                },
				tooltip: {
					formatter: null
				},
                series: []
             };

            switch(type) {
                case 'day':
                    self.show_graph_day(now, graph_options);
                    break;
                case 'week':
                    self.show_graph_week(now, graph_options);
                    break;
                case 'month':
                    self.show_graph_month(now, graph_options);
                    break;
                case 'year':
                    self.show_graph_year(now, graph_options);
                    break;
            }
        },

        show_graph_day: function(now, graph_options) {
            var self = this, o = this.options;
            var from = new Date(now.getFullYear(), now.getMonth(), now.getDate(),0,0,0);
            var to = new Date(now.getFullYear(), now.getMonth(), now.getDate(),23,59,59);

            graph_options.title.text = Highcharts.dateFormat('%A %d %B %Y', now.getTime());
            graph_options.xAxis.min = Date.UTC(now.getFullYear(), now.getMonth(), now.getDate());
            graph_options.xAxis.max = Date.UTC(now.getFullYear(), now.getMonth(), now.getDate(), 23,59,59);
            graph_options.tooltip.formatter = function() {
			                return Highcharts.dateFormat('%d/%m/%Y %Hh', this.x) +'<br/>'
                                + "<strong>" + Highcharts.numberFormat(this.y, 2, ',') +" " + o.model_parameters.unit + "</strong>";
                        }

            $.getREST(['stats', o.deviceid, o.key, 'from', Math.round(from.getTime() / 1000), 'to', Math.round(to.getTime() / 1000),'interval', 'hour', 'selector', 'avg'],
                function(data) {
                    var status = (data.status).toLowerCase();
                    if (status == 'ok') {
                        var d = [];
                        var values = data.stats[0].values;
                        $.each(values, function(index, stat) {
                            d.push([(Date.UTC(stat[0], stat[1]-1, stat[3], stat[4], 0, 0)), stat[5]]);
                        });
                        graph_options.series.push({name:o.featurename,data: d});
                        var chart = new Highcharts.Chart(graph_options);
                    } else {
                        $.notification('error', '{% trans "data creation failed" %} (' + data.description + ')');                                                                      
                    }
                }
            );
        },

        show_graph_week: function(now, graph_options) {
            var self = this, o = this.options;
            var from = new Date(now.getFullYear(), now.getMonth(), now.getDate() - now.getDay(),0,0,0);
            var to = new Date(now.getFullYear(), now.getMonth(), now.getDate() - now.getDay() + 6,23,59,59);

            graph_options.title.text = Highcharts.dateFormat('%A %d %B %Y', now.getTime());
            graph_options.xAxis.min = Date.UTC(from.getFullYear(), from.getMonth(), from.getDate());
            graph_options.xAxis.max = Date.UTC(to.getFullYear(), to.getMonth(), to.getDate(),23,59,59);
            graph_options.xAxis.dateTimeLabelFormats = {day: '%A %e'};
            graph_options.tooltip.formatter = function() {
			                return Highcharts.dateFormat('%d/%m/%Y %Hh', this.x) +'<br/>'
                                + "<strong>" + Highcharts.numberFormat(this.y, 2, ',') +" " + o.model_parameters.unit + "</strong>";
                        }

            $.getREST(['stats', o.deviceid, o.key, 'from', Math.round(from.getTime() / 1000), 'to', Math.round(to.getTime() / 1000),'interval', 'hour', 'selector', 'avg'],
                function(data) {
                    var status = (data.status).toLowerCase();
                    if (status == 'ok') {
                        var d = [];
                        var values = data.stats[0].values;
                        $.each(values, function(index, stat) {
                            d.push([(Date.UTC(stat[0], stat[1]-1, stat[3], stat[4], 0, 0)), stat[5]]);
                        });
                        graph_options.series.push({name:o.featurename,data: d});
                        var chart = new Highcharts.Chart(graph_options);
                    } else {
                        $.notification('error', '{% trans "data creation failed" %} (' + data.description + ')');                                                                      
                    }
                }
            );
        },

        show_graph_month: function(now, graph_options) {
            var self = this, o = this.options;
            var from = new Date(now.getFullYear(), now.getMonth(), 1,0,0,0);
            var to = new Date(now.getFullYear(), now.getMonth(), 31,23,59,59);

            graph_options.title.text = Highcharts.dateFormat('%B %Y', now.getTime())
            graph_options.xAxis.min = Date.UTC(now.getFullYear(), now.getMonth(), 1);
            graph_options.xAxis.max = Date.UTC(now.getFullYear(), now.getMonth(), 31, 23,59,59);
            graph_options.tooltip.formatter = function() {
			                return Highcharts.dateFormat('%d/%m/%Y', this.x) +'<br/>'
                                + "<strong>" + Highcharts.numberFormat(this.y, 2, ',') +" " + o.model_parameters.unit + "</strong>";
                        }

            $.getREST(['stats', o.deviceid, o.key, 'from', Math.round(from.getTime() / 1000), 'to', Math.round(to.getTime() / 1000),'interval', 'day', 'selector', 'avg'],
                function(data) {
                    var status = (data.status).toLowerCase();
                    if (status == 'ok') {
                        var d = [];
                        var values = data.stats[0].values;
                        $.each(values, function(index, stat) {
                            d.push([(Date.UTC(stat[0], stat[1]-1, stat[3], 0, 0, 0)), stat[4]]);
                        });
                        graph_options.series.push({name:o.featurename,data: d});
                        var chart = new Highcharts.Chart(graph_options);
                    } else {
                        $.notification('error', '{% trans "data creation failed" %} (' + data.description + ')');                                                                      
                    }
                }
            );
        },

        show_graph_year: function(now, graph_options) {
            var self = this, o = this.options;
            var from = new Date(now.getFullYear(), 0, 1,0,0,0);
            var to = new Date(now.getFullYear(), 11, 31,23,59,59);
            
            graph_options.title.text = Highcharts.dateFormat('%Y', now.getTime())
            graph_options.xAxis.min = Date.UTC(now.getFullYear(), 0, 1);
            graph_options.xAxis.max = Date.UTC(now.getFullYear(), 11, 31, 23,59,59);
            graph_options.tooltip.formatter = function() {
			                return Highcharts.dateFormat('%d/%m/%Y', this.x) +'<br/>'
                                + "<strong>" + Highcharts.numberFormat(this.y, 2, ',') +" " + o.model_parameters.unit + "</strong>";
                        }

            $.getREST(['stats', o.deviceid, o.key, 'from', Math.round(from.getTime() / 1000), 'to', Math.round(to.getTime() / 1000),'interval', 'day', 'selector', 'avg'],
                function(data) {
                    var status = (data.status).toLowerCase();
                    if (status == 'ok') {
                        var d = [];
                        var values = data.stats[0].values;
                        $.each(values, function(index, stat) {
                            d.push([(Date.UTC(stat[0], stat[1]-1, stat[3], 0, 0, 0)), stat[4]]);
                        });
                        graph_options.series.push({name:o.featurename,data: d});
                        var chart = new Highcharts.Chart(graph_options);
                    } else {
                        $.notification('error', '{% trans "data creation failed" %} (' + data.description + ')');                                                                      
                    }
                }
            );
        }
    });
})(jQuery);