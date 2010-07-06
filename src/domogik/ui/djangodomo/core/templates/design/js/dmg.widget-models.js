(function($) {
    /* Mini Widget */
    $.ui.widget.subclass("ui.widget_models", {
        // default options
        options: {
        },

        _init: function() {
            var self = this, o = this.options;
	    this.element.empty();
	    var widget = $("<li class='widget'>1x1</li>");
	    widget.draggable({
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
            var identity = $("<canvas class='identity' width='60' height='60'></canvas>")
	    widget.append(identity);
//	    li.append(widget);
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