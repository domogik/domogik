var widgets_list = {
    'sensor.boolean': [],
    'sensor.number': [],
    'sensor.string': [],
    'actuator.binary': [],
    'actuator.range': [],
    'actuator.number': [],
    'actuator.trigger': [],
    'actuator.string': []
};

var widgets_options = {};

function register_widget(type, id, options) {
    widgets_list[type].push(id);
    widgets_options[id] = options;
}

function get_widgets(type) {
    return widgets_list[type];
}

function get_widgets_options(id) {
    return widgets_options[id];
}

(function($) {
    
    $.extend({
        create_widget : function(data) {
            $.ui.widget_core.subclass('ui.' + data.options.id, data);
            register_widget(data.options.type, data.options.id, data.options);
        },
        
        create_widget_1x1_extended : function(data) {
            $.ui.widget_1x1_extended.subclass('ui.' + data.options.id, data);
            register_widget(data.options.type, data.options.id, data.options);
        }
    });
    
    $.ui.widget.subclass("ui.widget_core", {
        // default options
        options: {
            creator: 'Unknown',
            name: 'Unknown',
            description: 'Unknown',
            filters: null,
            width: 1,
            height: 1,
            key: '',
            displayname: true,
            displayborder: true,
            screenshot: null
        },
    
        _init: function() {
            var self = this, o = this.options;
            var types = o.type.split('.');
            this.element.addClass('widget')
                .addClass(o.id)
                .addClass(types[0])
                .addClass(types[1])
                .addClass('size' + o.width + 'x' + o.height)
                .attr("tabindex", 0);
            if (o.displayborder) {
                this.element.addClass('border');
            }
            if (o.displayname) {
                this._devicename = $("<div class='identity identitydevice length" + o.width + "'>" + o.devicename + "</div>");
                this.element.append(this._devicename);
                this._featurename = $("<div class='identity identityfeature length" + o.height + "'>" + o.featurename + "</div>");
                this.element.append(this._featurename);
            }
            
            $(document).bind('dmg_event', function(event, data) {
                self._eventsHandler(data);
            });
        },
        
        _initValues: function(nb) {
            var self = this, o = this.options;
            rest.get(['stats', o.deviceid, o.key, 'last', nb],
                function(data) {
                    var status = (data.status).toLowerCase();
                    if (status == 'ok') {
                        self._statsHandler(data.stats);
                    } else {
                        $.notification('error', '{% trans "Getting stats failed" %} (' + data.description + ')');
                    }
                }
            );
        },
        
        _eventsHandler: function(events) {
            var self = this, o = this.options;
            if (events.device_id == o.deviceid) {
                $.each(events.data, function(index, data) {
                    if (data.key.toLowerCase() == o.key.toLowerCase()) {
                        self._eventHandler(events.timestamp, data.value);
                    }
                });
            }
        },
        
        _statsHandler: function(stats) {
        },
        
        _eventHandler: function(timestamp, value) {
        }
    });
})(jQuery);
