(function($) {
    $.extend({
	    getJson: function(string){
            var decoded = $('<div></div>').html(string).text();
            console.debug(decoded); // Firebug
            return eval('(' + decoded+ ')');
        }
    });
})(jQuery);
