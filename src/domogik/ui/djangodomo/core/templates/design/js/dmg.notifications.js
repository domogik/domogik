(function($) {
    $.jGrowl.defaults.closerTemplate = '<div>hide all notifications</div>';

    $.extend({
        notification: function(status, msg) {
            var header = null;
            var theme = status;
            var sticky = false;
            switch (theme) {
                case 'ok':
                    header = "Confirmation";
                    break;
                case 'info':
                    header = "Information";
                    sticky = true;
                    break;
                case 'error':
                    header = "Error";
                    sticky = true;
                    break;
                case 'warning':
                    header = "Warning";
                    sticky = true;
                    break;
            }    
            $.jGrowl(msg, { header: header, sticky: sticky, theme: theme });
        }
    });
})(jQuery);

