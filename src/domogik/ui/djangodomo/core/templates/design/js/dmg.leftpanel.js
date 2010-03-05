(function($) {
    $.fn.extend({
	    leftpanel: function(options){
            var self = this;
            $(options.openbutton).click(function() {
                $(".extended").hide();
                $(self).show();
            });
            var close = $("<button class='leftpanelbutton'>" + options.closetext + "</button>");
            close.click(function() {
                $(self).hide();                                    
            });
        
            $(this)
                .hide()
                .prepend(close);
        }
    });
})(jQuery);

