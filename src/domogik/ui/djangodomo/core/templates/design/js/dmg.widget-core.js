var widgets_list = {
	'sensor.boolean': [],
	'sensor.number': [],
	'sensor.string': [],
	'actuator.binary': [],
	'actuator.range': [],
	'actuator.trigger': []
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
            filter: {techno:'',device:'',feature:''},
            width: 1,
            height: 1,
			displayname: true,
			displayborder: true
        },
		
		_init: function() {
			var self = this, o = this.options;
            this.element.addClass('widget')
				.addClass(o.id)
				.addClass('size' + o.width + 'x' + o.height)
                .attr("tabindex", 0);
			if (o.displayname) {
	            this._identity = $("<canvas class='identity' width='60' height='60'></canvas>")
	            this.element.append(this._identity);				
				var canvas = this._identity.get(0);
				if (canvas.getContext){
					var ctx = canvas.getContext('2d');
					ctx.beginPath();
					ctx.font = "6pt Arial";
					ctx.textBaseline = "top"
					ctx.fillText(o.devicename, 15, 5);
					ctx.translate(5,60);
					ctx.rotate(-(Math.PI/2));
					ctx.fillText(o.featurename, 0, 0);  
				}
			}
		}
    });
})(jQuery);