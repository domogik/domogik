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
                var model = $("<li>1x1</li>");
                var woptions = {
                    featurevalue: o.featurevalue,
                    featurename: o.featurename,
                    devicevalue: o.devicevalue,
                    devicename: o.devicename
                }
                eval("model." + id + "();");
                eval("model." + id + "('model', woptions);");
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
})(jQuery);