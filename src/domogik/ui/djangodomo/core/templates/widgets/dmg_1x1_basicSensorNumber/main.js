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

        graph: null,
        graph_options: null,
        now : null,
        
        _init: function() {
            var self = this, o = this.options;
            
            if (!o.model_parameters.unit) o.model_parameters.unit = ''; // if unit not defined, display ''
            
            this.element.addClass("icon32-usage-" + o.usage)
                .addClass('clickable');
            this._value =  $("<div class='value'></div>");
            this.element.append(this._value);

            this._status = $.getStatus();
            this.element.append(this._status);
            
            this._panel = $.getPanel({width:190, height:190, circle: {start:140, end:90}});
            this.element.append(this._panel);
            this._panel.panelAddCommand({label:'Close', showlabel: false, className:'close', r:70, deg:140, rotate:false, click:function(e){self.close();e.stopPropagation();}});
            this._panel.panelAddCommand({label:'Charts', showlabel: true, className:'graph', r:70, deg:-30, rotate:false, click:function(e){self.open_graph();e.stopPropagation();}});
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

        open_graph: function() {
            var self = this, o = this.options;
            this.close();
    
            this.now = new Date();

            this.graph_options = {
                chart: {
                   renderTo: 'dialog-graph',
                   borderRadius: null,
                   backgroundColor:'#eeeeee',
                   type: 'line'
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
                    min: null,
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
                plotOptions: {
                    line: {
                        marker: {
                            enabled: false,
                            states: {
                                hover: {
                                   enabled: true
                                }
                            }   
                        }
                    }
                }
            };

            var dialog = $("<div id='dialog' title='Charts'><ul id='dialog-nav'></ul><div id='dialog-graph' style='width:100%;height:100%;'></div></div>");
            var year = $("<li class='btyear'><button>Year</button></li>");
            year.click(function() {
                self.show_graph('year', 0);
            });
            var month = $("<li class='btmonth'><button>Month</button></li>");
            month.click(function() {
                self.show_graph('month', 0);
            });
            var week = $("<li class='bt7d'><button>Last 7 days</button></li>");
            week.click(function() {
                self.show_graph('7d', 0);
            });
            var day = $("<li class='bt24h'><button>Last 24 hours</button></li>");
            day.click(function() {
                self.show_graph('24h', 0);
            });            
            var previous = $("<li class='previous'><button disabled='disabled'>Previous</button></li>");
            var next = $("<li class='next'><button disabled='disabled'>Next</button></li>");

            dialog.find('#dialog-nav')
                .append(previous)
                .append(next)
                .append(year)
                .append(month)
                .append(week)
                .append(day);

            $('body').append(dialog);
            dialog.dialog({ width:'90%',
                position: ['middle', 50],
                resizable: false,
                modal: true,
                close: function(ev, ui) {
                    $(this).remove();
                }
            });
            day.find('button').focus();
            this.show_graph('24h', 0);
        },
        
        show_graph: function(type, shift) {
            var self = this, o = this.options;
            if (this.graph) this.graph.destroy();
            $('#dialog-nav button').attr('disabled', 'disabled');
            $('#dialog-nav button.active').removeClass('active');
            $('#dialog-nav li.bt' + type + ' button').addClass('active');
            
            $('#dialog-nav li.previous button').unbind('click').click(function() {
                self.show_graph(type, shift+1);
            });
            if (shift > 0) {
                $('#dialog-nav li.next button').unbind('click').click(function() {
                    self.show_graph(type, shift-1);
                });
            }

            var restparams = null
            switch(type) {
                case '24h':
                    restparams = this.init_graph_24h(shift);
                    break;
                case '7d':
                    restparams = this.init_graph_7d(shift);
                    break;
                case 'month':
                    restparams = this.init_graph_month(shift);
                    break;
                case 'year':
                    restparams = this.init_graph_year(shift);
                    break;
            }
            this.graph = new Highcharts.Chart(this.graph_options);
            this.graph.showLoading();

            rest.get(restparams,
                function(data) {
                    var status = (data.status).toLowerCase();
                    if (status == 'ok') {
                        var d = null;
                        switch(type) {
                            case '24h':
                                d = self.get_graph_24h(data.stats[0].values);
                                break;
                            case '7d':
                                d = self.get_graph_7d(data.stats[0].values);
                                break;
                            case 'month':
                                d = self.get_graph_month(data.stats[0].values);
                                break;
                            case 'year':
                                d = self.get_graph_year(data.stats[0].values);
                                break;
                        }
                        self.graph.yAxis[0].addPlotLine({
                            value: data.stats[0].global_values.avg,
                            color: '#660099',
                            width: 1,
                            label:{
                                     text: 'Avg: ' + Highcharts.numberFormat(data.stats[0].global_values.avg, 2) +" " + o.model_parameters.unit,
                                     align: 'right'
                                 }
                        });
                        self.graph.yAxis[0].addPlotLine({
                            value: data.stats[0].global_values.min,
                            color: '#0000cc',
                            width: 1,
                            label:{
                                     text: 'Min: ' + Highcharts.numberFormat(data.stats[0].global_values.min, 2) +" " + o.model_parameters.unit,
                                     align: 'right'
                                 }
                        });
                        self.graph.yAxis[0].addPlotLine({
                            value: data.stats[0].global_values.max,
                            color: '#cc0000',
                            width: 1,
                            label:{
                                     text: 'Max: ' + Highcharts.numberFormat(data.stats[0].global_values.max, 2) +" " + o.model_parameters.unit,
                                     align: 'right'
                                 }
                        });                        self.graph.addSeries({name:o.featurename,data: d});
                        self.graph.addSeries({data: [0]}); // for min
                        self.graph.addSeries({data: [data.stats[0].global_values.max]}); // for max
                    } else {
                        $.notification('error', '{% trans "data creation failed" %} (' + data.description + ')');                                                                      
                    }
                    self.graph.hideLoading();
                    $('#dialog-nav button').removeAttr('disabled');
                    if (shift == 0) $('#dialog-nav li.next button').attr('disabled', 'disabled');
                }
            );
        },

        init_graph_24h: function(shift) {
            var self = this, o = this.options;

            var from = new Date(this.now.getFullYear(), this.now.getMonth(), this.now.getDate()-1-shift,this.now.getHours(),0,0);
            var to = new Date(this.now.getFullYear(), this.now.getMonth(), this.now.getDate()-shift,this.now.getHours()+1,0,0);

            this.graph_options.title.text = Highcharts.dateFormat('%A %d %B %Y', to.getTime());
            this.graph_options.xAxis.min = Date.UTC(from.getFullYear(), from.getMonth(), from.getDate(),from.getHours(),0,0);
            this.graph_options.xAxis.max = Date.UTC(to.getFullYear(), to.getMonth(), to.getDate(),to.getHours(),0,0);
            this.graph_options.xAxis.dateTimeLabelFormats = {hour: '%H:%M'};
            this.graph_options.xAxis.tickInterval = null;
            this.graph_options.tooltip.formatter = function() {
			                return Highcharts.dateFormat('%d/%m/%Y %Hh%M', this.x) +'<br/>'
                                + "<strong>" + Highcharts.numberFormat(this.y, 2, ',') +" " + o.model_parameters.unit + "</strong>";
                        };
            return ['stats', o.deviceid, o.key, 'from', Math.round(from.getTime() / 1000), 'to', Math.round(to.getTime() / 1000),'interval', 'minute', 'selector', 'avg'];
        },
        
        get_graph_24h: function(values) {
            var d = [];
            $.each(values, function(index, stat) {
                d.push([(Date.UTC(stat[0], stat[1]-1, stat[3], stat[4], stat[5], 0)), stat[6]]);
            });
            return d;
        },

        init_graph_7d: function(shift, now) {
            var self = this, o = this.options;

            var from =new Date(this.now.getFullYear(), this.now.getMonth(), this.now.getDate()-(7*(shift+1)),this.now.getHours(),0,0);
            var to = new Date(this.now.getFullYear(), this.now.getMonth(), this.now.getDate()-(7*shift),this.now.getHours()+1,0,0);

            this.graph_options.title.text = Highcharts.dateFormat('%d/%m/%Y', from.getTime()) + " - " + Highcharts.dateFormat('%d/%m/%Y', to.getTime());
            this.graph_options.xAxis.min = Date.UTC(from.getFullYear(), from.getMonth(), from.getDate(), from.getHours(),0,0);
            this.graph_options.xAxis.max = Date.UTC(to.getFullYear(), to.getMonth(), to.getDate(), to.getHours()+1,0,0);
            this.graph_options.xAxis.dateTimeLabelFormats = {day: '%A %e'};
            this.graph_options.xAxis.tickInterval = 24 * 3600 * 1000; // a day
            this.graph_options.tooltip.formatter = function() {
			                return Highcharts.dateFormat('%d/%m/%Y %Hh', this.x) +'<br/>'
                                + "<strong>" + Highcharts.numberFormat(this.y, 2, ',') +" " + o.model_parameters.unit + "</strong>";
                        };
            return ['stats', o.deviceid, o.key, 'from', Math.round(from.getTime() / 1000), 'to', Math.round(to.getTime() / 1000),'interval', 'hour', 'selector', 'avg'];
        },

        get_graph_7d: function(values) {
            var d = [];
            $.each(values, function(index, stat) {
                d.push([(Date.UTC(stat[0], stat[1]-1, stat[3], stat[4], 0, 0)), stat[5]]);
            });
            return d;
        },

        init_graph_month: function(shift) {
            var self = this, o = this.options;
            
            var lastDayMonth = (new Date((new Date(this.now.getFullYear(), this.now.getMonth()-shift+1,1))-1)).getDate();
            
            var from = new Date(this.now.getFullYear(), this.now.getMonth()-shift, 1,0,0,0);
            var to = new Date(this.now.getFullYear(), this.now.getMonth()-shift, lastDayMonth,23,59,59);

            this.graph_options.title.text = Highcharts.dateFormat('%B %Y', to.getTime())
            this.graph_options.xAxis.min = Date.UTC(from.getFullYear(), from.getMonth(), 1);
            this.graph_options.xAxis.max = Date.UTC(to.getFullYear(), to.getMonth(), 31, 23,59,59);
            this.graph_options.xAxis.dateTimeLabelFormats = {day: '%e. %b'};
            this.graph_options.xAxis.tickInterval = null;
            this.graph_options.tooltip.formatter = function() {
			                return Highcharts.dateFormat('%d/%m/%Y', this.x) +'<br/>'
                                + "<strong>" + Highcharts.numberFormat(this.y, 2, ',') +" " + o.model_parameters.unit + "</strong>";
                        };
            return ['stats', o.deviceid, o.key, 'from', Math.round(from.getTime() / 1000), 'to', Math.round(to.getTime() / 1000),'interval', 'day', 'selector', 'avg'];
        },

        get_graph_month: function(values) {
            var d = [];
            $.each(values, function(index, stat) {
                d.push([(Date.UTC(stat[0], stat[1]-1, stat[3], 0, 0, 0)), stat[4]]);
            });
            return d;
        },
        
        init_graph_year: function(shift) {
            var self = this, o = this.options;

            var from = new Date(this.now.getFullYear()-shift, 0, 1,0,0,0);
            var to = new Date(this.now.getFullYear()-shift, 11, 31,23,59,59);
            
            this.graph_options.title.text = Highcharts.dateFormat('%Y', to.getTime())
            this.graph_options.xAxis.min = Date.UTC(from.getFullYear(), 0, 1);
            this.graph_options.xAxis.max = Date.UTC(to.getFullYear(), 11, 31, 23,59,59);
            this.graph_options.xAxis.dateTimeLabelFormats = {month: '%b %y'};
            this.graph_options.xAxis.tickInterval = null;
            this.graph_options.tooltip.formatter = function() {
			                return Highcharts.dateFormat('%d/%m/%Y', this.x) +'<br/>'
                                + "<strong>" + Highcharts.numberFormat(this.y, 2, ',') +" " + o.model_parameters.unit + "</strong>";
                        };
            return ['stats', o.deviceid, o.key, 'from', Math.round(from.getTime() / 1000), 'to', Math.round(to.getTime() / 1000),'interval', 'day', 'selector', 'avg'];
        },

        get_graph_year: function(values) {
            var d = [];
            $.each(values, function(index, stat) {
                d.push([(Date.UTC(stat[0], stat[1]-1, stat[3], 0, 0, 0)), stat[4]]);
            });
            return d;
        }
    });
})(jQuery);