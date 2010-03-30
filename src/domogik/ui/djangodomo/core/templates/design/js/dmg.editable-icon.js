(function($) {
    $.widget("ui.editable_icon", {
        _init: function() {
            var self = this, o = this.options;
            this.original_icon = o.icon;
            this.current_icon = o.icon;
            this.editMode = false;
            this.element.addClass('editable_icon').addClass("icon64-" + o.type + "-" + this.current_icon);
            this.element.keypress(function (e) {
                if(self.editMode) { // Edit mode
                    switch(e.keyCode) {
                        case 37: // left arrow
                            self._previous();
                            break;					
                        case 39: // right arrow
                            self._next();
                            break;					                        
                        case 27: // escape
                            self._cancel();    
                            break;					
                        case 13: // Enter
                        case 32: // Space
                            self._submit();    
                            break;
                    };                    
                } else { // Display mode
                    switch(e.keyCode) {
                        case 13: // Enter
                        case 32: // Space
                            self._edit_mode();    
                            break;
                    };
                }
                e.stopPropagation();
            });

            this.element.attr('tabindex', '0');
            this.button_edit = $("<div class='icon16-action-update button-edit'><span class='offscreen'>" + o.editText + "</span></div>");
            this.button_edit.click(function() {
                self._edit_mode();
            });
            this.button_previous = $("<div class='icon16-action-previous button-previous hidden'><span class='offscreen'>" + o.previousText + "</span></div>");
            this.button_previous.click(function() {
                self._previous();
            });
            this.button_next = $("<div class='icon16-action-next button-next hidden'><span class='offscreen'>" + o.nextText + "</span></div>");
            this.button_next.click(function() {
                self._next();
            });
            this.button_submit = $("<div class='icon16-action-submit button-submit hidden'><span class='offscreen'>" + o.validText + "</span></div>");
            this.button_submit.click(function() {
                self._submit();
            });
            this.button_cancel = $("<div class='icon16-action-cancel button-cancel hidden'><span class='offscreen'>" + o.cancelText + "</span></div>");
            this.button_cancel.click(function() {
                self._cancel();
            });
            this.element.append(this.button_edit);
            this.element.append(this.button_previous);
            this.element.append(this.button_next);
            this.element.append(this.button_submit);
            this.element.append(this.button_cancel);
        },
        
        _next: function() {
            var self = this, o = this.options;
            this.element.removeClass("icon64-" + o.type + "-" + this.current_icon);
            this.current_index++;
            if (this.current_index > (o.list.length - 1)) this.current_index = 0;
            this.current_icon = o.list[this.current_index];
            this.element.addClass("icon64-" + o.type + "-" + this.current_icon);
        },
        
        _previous: function() {
            var self = this, o = this.options;
            this.element.removeClass("icon64-" + o.type + "-" + this.current_icon);
            this.current_index--;
            if (this.current_index < 0) this.current_index = o.list.length - 1;
            this.current_icon = o.list[this.current_index];
            this.element.addClass("icon64-" + o.type + "-" + this.current_icon);
        },
        
        _cancel: function() {
            var self = this, o = this.options;
            this._display_mode();
            this.element.removeClass("icon64-" + o.type + "-" + this.current_icon);
            this.cancel();
        },
        
        _submit: function() {
            var self = this, o = this.options;
            this._display_mode();
            this.element.removeClass("icon64-" + o.type + "-" + this.current_icon);
            o.validCallback(this, this.current_icon);
        },
        
        cancel: function() {
            this.current_icon = this.original_icon;
            this.element.addClass("icon64-" + this.options.type + "-" + this.original_icon);
        },
        
        valid: function() {
            this.element.addClass("icon64-" + this.options.type + "-" + this.current_icon);
        },
        
        _display_mode: function() {
            this.editMode = false;
            this.element.removeClass('edited');
            this.button_previous.addClass('hidden');
            this.button_next.addClass('hidden');
            this.button_submit.addClass('hidden');
            this.button_cancel.addClass('hidden');
            this.button_edit.removeClass('hidden');
        },
        
        _edit_mode: function() {
            this.editMode = true;
            var self = this, o = this.options;
            this.current_index = $.inArray(this.current_icon, o.list);
            if(this.current_index == -1) {
                this.original_icon = "";
            } else {
                this.original_icon = this.current_icon;
            }
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