(function($) {
    /* Mini Widget */
    $.ui.widget.subclass("ui.widget_models", {
        // default options
        options: {
        },

        _init: function() {
            var self = this, o = this.options;
            this.element.empty();
            var widgets = get_widgets(o.type);
            $.each(widgets, function(index, id){
                var model = $("<li></li>");
                model.widget_model({
                    id: id,
                    featurevalue: o.featurevalue,
                    featurename: o.featurename,
                    devicename: o.devicename
                });
                model.draggable({
                    helper: "clone",
                    revert: 'invalid',
                    appendTo: 'body',
                    drag: function(event, ui) {
                        $("#panel").hide();
                    },
                    stop: function(event, ui) {
                        $("#panel").show();
                        self._init();
                        if($(this).hasClass("success")) {
                            $(this).removeClass("success");
                        } else {
                            $(this).remove();			
                        }
                    }
                });
                self.element.append(model); 
            });
        },
	
        update: function() {
            this._init();
        }
    });
    
    $.ui.widget.subclass("ui.widget_model", {
        // default options
        options: {
        },

        _init: function() {
            var self = this, o = this.options;
            var woptions = get_widgets_options(o.id)
            if (woptions) {
                o = $.extend ({}, woptions, o);
            }

            this.element.addClass('model')
			    .attr("widgetid", o.id)
				.addClass('size' + o.width + 'x' + o.height)
                .attr("tabindex", 0)
	            .attr('featurevalue', o.featurevalue)
                .text(o.width + 'x' + o.height);
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
    });
})(jQuery);