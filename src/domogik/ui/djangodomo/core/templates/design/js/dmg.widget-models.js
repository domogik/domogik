(function($) {
    /* Mini Widget */
    $.ui.widget.subclass("ui.widget_models", {
        // default options
        options: {
        },

        _init: function() {
            var self = this, o = this.options;
	    this.element.empty();
	    this.element.widget_model({
                featurevalue: o.featurevalue,
                featurename: o.featurename,
                devicevalue: o.devicevalue,
                devicename: o.devicename,
		draggable: {
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
		}
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
	    var widget = $("<li class='widget'>1x1</li>")
		.attr('devicevalue', o.devicevalue)
		.attr('featurevalue', o.featurevalue);
	    widget.draggable(o.draggable);
            var identity = $("<canvas class='identity' width='60' height='60'></canvas>")
	    widget.append(identity);
	    this.element.append(widget);
            var canvas = identity.get(0);
            if (canvas.getContext){
                var ctx = canvas.getContext('2d');
                ctx.beginPath();
                ctx.font = "6pt Arial";
                ctx.textBaseline = "top"
                ctx.fillText(o.featurename, 15, 5);
                ctx.translate(5,60);
                ctx.rotate(-(Math.PI/2));
                ctx.fillText(o.devicename, 0, 0);  
            }
        }
    });
})(jQuery);