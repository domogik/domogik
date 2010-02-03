(function($) {
    $.widget("ui.domogik_tabs", {
        _init: function() {
            var self = this, o = this.options;
            this.list = this.element.children("ul:first");
            var addButton = $("<li><a href='#'><span>+</span></a></li>");
            addButton.click(o.addCallback);
            this.list.prepend(addButton);
        }
    });
    $.extend($.ui.domogik_tabs, {
        defaults: {
        	addCallback: null
        }
    });
})(jQuery);
