var widget_list = {
	'sensor.boolean': [],
	'sensor.number': [],
	'sensor.string': [],
	'actuator.binary': [],
	'actuator.range': [],
	'actuator.trigger': []
};

function register_widget(type, id) {
	widget_list[type].push(id);
}

function get_widgets(type) {
	return widget_list[type];
}

(function($) {	
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
		
		widget: function(params) {
			this.params = params;
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
					ctx.fillText(params.devicename, 15, 5);
					ctx.translate(5,60);
					ctx.rotate(-(Math.PI/2));
					ctx.fillText(params.featurename, 0, 0);  
				}
			}
		},
		
		model: function(params) {
            var self = this, o = this.options;
            this.element.addClass('model')
			    .attr("widgetid", o.id)
				.addClass('size' + o.width + 'x' + o.height)
                .attr("tabindex", 0)
				.attr('devicevalue', params.devicevalue)
	            .attr('featurevalue', params.featurevalue);
			this._identity = $("<canvas class='identity' width='60' height='60'></canvas>")
			this.element.append(this._identity);				
			var canvas = this._identity.get(0);
			if (canvas.getContext){
				var ctx = canvas.getContext('2d');
				ctx.beginPath();
				ctx.font = "6pt Arial";
				ctx.textBaseline = "top"
				ctx.fillText(params.devicename, 15, 5);
				ctx.translate(5,60);
				ctx.rotate(-(Math.PI/2));
				ctx.fillText(params.featurename, 0, 0);  
			}
		}
    });
})(jQuery);