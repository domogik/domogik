(function($) {
    $.widget("ui.domogik_tabs", {
        _init: function() {
            var self = this, o = this.options;
            this.list = this.element.children("ul:first");
            var addButton = $("<li><a href='#' id='" + o.addId + "' class='add icon16-action-add' title='"+ o.addTitle + "'>&nbsp;<span class='offscreen'>"+ o.addTitle + "</span></a></li>");
            this.list.prepend(addButton);
        }
    });
    $.extend($.ui.domogik_tabs, {
        defaults: {
            addTitle: "Add",
        	addCallback: null
        }
    });
})(jQuery);
