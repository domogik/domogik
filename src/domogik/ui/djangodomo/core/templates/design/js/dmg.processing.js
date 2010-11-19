(function($) {
    $.widget("ui.processing", {
        _init: function() {
            var width = this.element.css('width');
            var height = this.element.css('height');
            this.div = $("<div class='processing'></div>");
            this.div.css('position', 'absolute')
                .css('float', 'left')
                .css('-moz-box-shadow', '0 0 4em #BDCB2F')
                .css('-webkit-box-shadow', '0 0 4em #BDCB2F')
                .css('background', 'none')
                .css('width', width)
                .css('height', height)
                .css('display', 'none');
            this.element.prepend(this.div);
        },
        
        start: function() {
            var self = this;
            this.div.append("<span class='offscreen'>Processing</span>");
            $(this.div).fadeIn(500).fadeOut(500);
            $(this.div).everyTime(1200, 'processing', function (){
                $(self.div).fadeIn(500).fadeOut(500);
            });
        },
        
        stop: function() {
            $(this.div).stopTime('processing');
        }
    });
    $.extend($.ui.processing, {});
})(jQuery);
