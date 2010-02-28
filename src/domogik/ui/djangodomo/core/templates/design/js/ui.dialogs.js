// <![CDATA[
(function($) {
    $.widget("ui.dialog_confirmation", {
        _init: function() {
            var self = this, o = this.options;
            this.element.append("<p></p>");
            this.element.dialog({
                bgiframe: true,
                autoOpen: false,
                height: 100,
                modal: true,
                close: function() {}
            });
        return this;
        },
        
        addbutton: function(ops) {
            var self = this, o = this.options;
            $(ops.button).click(function() {
                self.element.dialog_confirmation('open', {
                    name: ops.name,
                    onok: ops.onok
                }); 
            });
        },
        
        open: function(ops) {
            var self = this, o = this.options;
            this.element.dialog('option', 'title', o.title + ' ' + ops.name);
            this.element.dialog('option', 'buttons', {
                'Yes': ops.onok,
                'No': function() {
                    $(this).dialog('close');
                }
            });
            $("p", this.element).text(o.content + ' ' + ops.name);
            this.element.dialog('open');
        }
    });
        
    $.extend($.ui.dialog_confirmation, {
        defaults: {
            title: '',
            content: ''
        }
    });
})(jQuery);
// ]]>