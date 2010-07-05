(function($) {
    /* Mini Widget */
    $.ui.widget.subclass("ui.widget_models", {
        // default options
        options: {
        },

        _init: function() {
            var self = this, o = this.options;
	    var li = $("<li class='widgetitem'></li>");
	    li.attr('ddvalue', '11');
	    li.attr('ddname', 'Creator - Name - 1x1');
	    var widget = $("<div class='widget'>1x1</div>");
            var identity = $("<canvas class='identity' width='60' height='60'></canvas>")
	    widget.append(identity);
	    li.append(widget);
	    this.element.append(li);
            
            var canvas = identity.get(0);
            if (canvas.getContext){
                var ctx = canvas.getContext('2d');
                ctx.beginPath();
                ctx.font = "6pt Arial";
                ctx.textBaseline = "top"
                ctx.fillText("name", 15, 5);
                ctx.translate(5,60);
                ctx.rotate(-(Math.PI/2));
                ctx.fillText("creator", 0, 0);  
            }
        }
    });
})(jQuery);