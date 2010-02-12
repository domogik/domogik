function updateTips(tips, t) {
    tips.text(t).effect("highlight", {},
    1500);
}

function checkLength(tips, o, n, min, max) {
    if (o.val().length > max || o.val().length < min) {
        o.addClass('ui-state-error');
        updateTips(tips, "La longueur de " + n + " doit tre comprise entre " + min + " et " + max + ".");
        return false;
    } else {
        return true;
    }

}

function updateTips(t) {
    tips.text(t).effect("highlight", {},
    1500);
}

function checkLength(o, n, min, max) {

    if (o.val().length > max || o.val().length < min) {
        o.addClass('ui-state-error');
        updateTips("La longueur de " + n + " doit tre comprise entre " + min + " et " + max + ".");
        return false;
    } else {
        return true;
    }

}

(function($) {
    $.widget("ui.editable_icon", {
        _init: function() {
            var self = this, o = this.options;
            this.original_icon = o.icon;
            this.current_icon = o.icon;
            this.element.addClass('editable_icon').addClass("icon64-" + o.type + "-" + this.current_icon);
            this.button_edit = $("<button class='icon16-action-update button-edit'><span class='offscreen'>" + o.editText + "</span></button>");
            this.button_edit.click(function() {
                self.current_index = $.inArray(self.current_icon, o.list);
                if(self.current_index == -1) {
                    self.original_icon = "";
                } else {
                    self.original_icon = self.current_icon;
                }
                self.edit_mode();
            });
            this.button_previous = $("<button class='icon16-action-previous button-previous hidden'><span class='offscreen'>" + o.previousText + "</span></button>");
            this.button_previous.click(function() {
                self.element.removeClass("icon64-" + o.type + "-" + self.current_icon);
                self.current_index--;
                if (self.current_index < 0) self.current_index = o.list.length - 1;
                self.current_icon = o.list[self.current_index];
                self.element.addClass("icon64-" + o.type + "-" + self.current_icon);
            });
            this.button_next = $("<button class='icon16-action-next button-next hidden'><span class='offscreen'>" + o.nextText + "</span></button>");
            this.button_next.click(function() {
                self.element.removeClass("icon64-" + o.type + "-" + self.current_icon);
                self.current_index++;
                if (self.current_index > (o.list.length - 1)) self.current_index = 0;
                self.current_icon = o.list[self.current_index];
                self.element.addClass("icon64-" + o.type + "-" + self.current_icon);
            });
            this.button_submit = $("<button class='icon16-action-submit button-submit hidden'><span class='offscreen'>" + o.validText + "</span></button>");
            this.button_submit.click(function() {
                self.display_mode();
                self.element.removeClass("icon64-" + o.type + "-" + self.current_icon);
                self.element.addClass("icon24-processing");
                o.validCallback(self, self.current_icon);
            });
            this.button_cancel = $("<button class='icon16-action-cancel button-cancel hidden'><span class='offscreen'>" + o.cancelText + "</span></button>");
            this.button_cancel.click(function() {
                self.display_mode();
                self.element.removeClass("icon64-" + o.type + "-" + self.current_icon);
                self.element.addClass("icon64-" + o.type + "-" + self.original_icon);
                self.current_icon = self.original_icon;
            });    
            this.element.append(this.button_edit);
            this.element.append(this.button_previous);
            this.element.append(this.button_next);
            this.element.append(this.button_submit);
            this.element.append(this.button_cancel);
        },
        
        cancel: function() {
            this.current_icon = this.original_icon;
            this.element.removeClass("icon24-processing");
            this.element.addClass("icon64-" + this.options.type + "-" + this.original_icon);
        },
        
        valid: function() {
            this.element.removeClass("icon24-processing");
            this.element.addClass("icon64-" + this.options.type + "-" + this.current_icon);
        },
        
        display_mode: function() {
            this.element.removeClass('edited');
            this.button_previous.addClass('hidden');
            this.button_next.addClass('hidden');
            this.button_submit.addClass('hidden');
            this.button_cancel.addClass('hidden');
            this.button_edit.removeClass('hidden');
        },
        
        edit_mode: function() {
            this.button_edit.addClass('hidden');
            this.element.addClass('edited');
            this.button_previous.removeClass('hidden');
            this.button_next.removeClass('hidden');
            this.button_submit.removeClass('hidden');
            this.button_cancel.removeClass('hidden');
        }
    });
    $.extend($.ui.editable_icon, {
        defaults: {
            icon: "",
            editText: "Edit icon",
            previousText: "View previous icon",
            nextText: "View next icon",
            validText: "Valid icon",
            cancelText: "Cancel icon change",
            validCallback: null
        }
    });
})(jQuery);