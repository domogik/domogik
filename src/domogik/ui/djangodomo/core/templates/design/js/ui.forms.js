function numbersonly(e) {
    var unicode=e.which;
    if (unicode!=8 && unicode!=0) { //if the key isn't the tab key
        if (unicode<48||unicode>57) {//if not a number return false //disable key press
            return false;
        } else {
            return true;
        }
    }
    return true;
}

(function($) {
    $.widget("ui.dialog_form", {
        _init: function() {
            var dialogheight = 110;
            var self = this, o = this.options;
            this.element.append("<ul id='" + o.tipsArea + "'>" + o.tips + "</ul>");
            var form = $("<form></form>");
            this._content = $("<fieldset></fieldset>");
            this._allFields = [];
            form.append(this._content);
            this.element.append(form);
            jQuery.each(o.fields, function(index, value) {
                var field = null;
                switch(value.type) {
                case 'text':
                    field = self._addTextField(value.name, value.label);
                    dialogheight += 50;
                    break;
                case 'numericpassword':
                    field = self._addNumericPasswordField(value.name, value.label);
                    dialogheight += 50;
                    break;
                case 'checkbox':
                    field = self._addCheckboxField(value.name, value.label);
                    dialogheight += 50;
                    break;
                case 'select':
                    field = self._addSelectField(value.name, value.label, value.option.initial, value.option.options);
                    dialogheight += 50;
                    break;
                case 'selectipod':
                    field = self._addSelectIpodField(value.name, value.label, value.option.initial, value.option.options);
                    dialogheight += 50;
                    break;
                }
                self._allFields.push(field);
            });
            
            this.element.dialog({
                bgiframe: true,
                autoOpen: false,
                height: dialogheight,
                modal: true,
                buttons: {
                    'OK': function() {
                        self._valid();
                    },
                    'Cancel': function() {
                        $(this).dialog('close');
                    }
                },
                close: function() {
                    $.each(self._allFields, function() {$(this).val('').removeClass('ui-state-error')});
                }
            });
        return this;
        },
        
        _addTextField: function(name, label) {
            this._content.append("<label class='medium' for='" + name + "'>" + label + "</label>");
            var input = $("<input type='text' class='medium' id='" + name + "' name='" + name + "' />");
            this._content.append(input);
            return input;
        },
        
        _addNumericPasswordField: function(name, label) {
            this._content.append("<label class='medium' for='" + name + "'>" + label + "</label>");
            var input = $("<input type='text' onkeypress='return numbersonly(event)' class='medium' id='" + name + "' name='" + name + "' />");
            this._content.append(input);
            return input;
        },

        _addCheckboxField: function(name, label) {
            this._content.append("<label class='medium' for='" + name + "'>" + label + "</label>");
            var input = $("<input type='checkbox' class='medium' id='" + name + "' name='" + name + "' />");
            this._content.append(input);
            return input;
        },
        
        _addSelectField: function(name, label, initial, options) {
            this._content.append("<label class='medium' for='" + name + "'>" + label + "</label>");
            var input = $("<select class='medium' id='" + name + "' name='" + name + "'></select>");
            if (initial) {
                input.append("<option value='" + initial.value + "'>" + initial.label + "</option>");
            }
            if (options) {
                jQuery.each(options, function(index, option) {
                    input.append("<option value='" + option.value + "'>" + option.label + "</option>");
                });                
            }
            this._content.append(input);
            return input;
        },
        
        _addSelectIpodField: function(name, label, initial, options) {
            this._content.append("<label class='medium' for='" + name + "'>" + label + "</label>");
            var input = $("<input type='hidden' class='medium' id='" + name + "' name='" + name + "' value='" + initial.value + "' />");
            this._content.append(input);
            var button = $("<a tabindex='0' href='#" + name + "_list' class='fg-button' id='" + name + "_button'>" + initial.label + "</a>");
            this._content.append(button);
            var list = $("<div id='" + name + "_list' class='offscreen'></div>");
            if (options) {
                var ul = $("<ul></ul>");
                jQuery.each(options, function(index, option) {
                    var li = $("<li></li>");
                    li.append("<a href='#'><div class='icon16-text " + option.icon + "'>" + option.label + "</div></a>");
                    if(option.submenu) {
                        var subul = $("<ul></ul>");
                        jQuery.each(option.submenu, function(index, suboption) {
                            subul.append("<li><a href='#' value='" + suboption.value + "' valuetxt='" + option.label + "." + suboption.label + "'>" + suboption.label + "</a></li>");
                        });
                        li.append(subul);
                    }
                    ul.append(li);
                });                
                list.append(ul);
            }
            this._content.append(list);
            button.menu({
                content: list.html(),
                backLink: false,
                crumbDefaultText: 'Choose an technologie:',
                resultValueField: '#' + name,
                resultTextElement: "#" + name + "_button"
            });
            return input;
        },
        
        _clearTips: function() {
            var self = this, o = this.options;
            $("#" + o.tipsArea + " li").remove();
        },
        
        _addTips: function(text) {
            var self = this, o = this.options;
            $("#" + o.tipsArea).append("<li>" + text + "</li>");            
        },
        
        _valid: function() {
            var self = this, o = this.options;
            self._clearTips();
            var valid = true;
            $(this._allFields).removeClass('ui-state-error');
            jQuery.each(o.fields, function(index, value) {
                switch(value.type) {
                case 'text':
                    if (!self._validTextLength(value.name, value.option.min, value.option.max)) {
                        $("#" + value.name).addClass('ui-state-error');
                        valid &= self._addTips(value.label + " length has to be between " + value.option. min + " and " + value.option.max + ".");
                    }
                    break;
                case 'numericpassword':
                    if (!self._validTextLength(value.name, value.option.min, value.option.max)) {
                        $("#" + value.name).addClass('ui-state-error');
                        valid &= self._addTips(value.label + " length has to be between " + value.option. min + " and " + value.option.max + ".");
                    }
                    break;
                case 'select':
                case 'selectipod':
                    if (!self._validNotInitial(value.name, value.option.initial)) {
                        $("#" + value.name + "_button").addClass('ui-state-error');
                        valid &= self._addTips(value.label + " is not selected");
                    }
                    break;                }
            });
            return valid;
        },

        _validTextLength: function(name, min, max) {
            var val = $("#" + name).val();
            return (val.length <= max && val.length >= min);
        },

        _validNotInitial: function(name, initial) {
            var val = $("#" + name).val();
            return (val != initial.value);
        },

        _values: function() {
            var self = this, o = this.options;
            var result = new Object();
            jQuery.each(o.fields, function(index, value) {
                switch(value.type) {
                case 'text':
                case 'numericpassword':
                case 'select':
                case 'selectipod':
                    result[value.name] = $('#' + value.name).val();
                    break;
                case 'checkbox':
                    result[value.name] = ($('#' + value.name).is(':checked'))?'True':'False';
                    break;
                }
            });
            return result;
        },
        
        addbutton: function(ops) {
            var self = this, o = this.options;
            $(ops.button).click(function() {
                self.element.dialog_form('open', {
                    title: ops.title,
                    onok: ops.onok
                }); 
            });
        },

        updbutton: function(ops) {
            var self = this, o = this.options;
            $(ops.button).click(function() {
                self.element.dialog_form('open', {
                    title: ops.title,
                    onok: ops.onok,
                    values: ops.values
                }); 
            });
        },
        
        open: function(ops) {
            var self = this, o = this.options;
            this.element.dialog('option', 'title', ops.title);
            this.element.dialog('option', 'buttons', {
                'Yes': function() {
                    if (self._valid()) {
                        var values = self._values();
                        ops.onok(values);                        
                    }
                },
                'Cancel': function() {
                    $(this).dialog('close');
                }
            });
            if (ops.values) {
                jQuery.each(o.fields, function(index, value) {
                    switch(value.type) {
                    case 'text':
                    case 'select':
                        $('#' + value.name).val(ops.values[value.name]);
                        break;
                    case 'checkbox':
                        if (ops.values[value.name] == true)
                            $('#' + value.name).attr('checked', 'checked');
                        break;
                    case 'selectipod':
                        $('#' + value.name).val(ops.values[value.name]);
                        var valuetxt = $('#' + value.name + "_list a[value = '" + ops.values[value.name] + "']").attr('valuetxt');
                        $('#' + value.name + '_button').text(valuetxt);
                        break;
                    }
                });
            }
            this.element.dialog('open');
        }
    });
        
    $.extend($.ui.dialog_form, {
        defaults: {
        }
    });

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
            this.element.addClass("icon64-" + this.options.type + "-" + this.original_icon);
        },
        
        valid: function() {
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