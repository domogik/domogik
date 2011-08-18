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
            var self = this, o = this.options;
            this.element.append("<div class='tip'>" + o.tips + "</div><ul class='tip' id='" + o.tipsid + "'></ul>");
            var form = $("<form></form>");
            this._content = $("<fieldset></fieldset>");
            this._allFields = [];
            form.append(this._content);
            this.element.append(form);
            jQuery.each(o.fields, function(index, value) {
                var field = null;
                switch(value.type) {
                case 'text':
                    field = self._addTextField(value.name, value.label, value.required);
                    break;
                case 'numericpassword':
                    field = self._addNumericPasswordField(value.name, value.label, value.required);
                    break;
                case 'checkbox':
                    field = self._addCheckboxField(value.name, value.label, value.required);
                    break;
                case 'select':
                    field = self._addSelectField(value.name, value.label, value.required, value.option.initial, value.option.options);
                    break;
                case 'selectipod':
                    field = self._addSelectIpodField(value.name, value.label, value.required, value.option.initial, value.option.options);
                    break;
                }
                self._allFields.push(field);
            });
            
            this.element.dialog({
                autoOpen: false,
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
        
        _addTextField: function(name, label, required) {
            var labelitem = $("<label for='" + name + "'>" + label + "</label>");
            var inputitem = $("<input type='text' class='medium' id='" + name + "' name='" + name + "' />");
            if (required) {
                labelitem.addClass('required');
                inputitem.addClass('required');
            }
            this._content.append(labelitem);
            this._content.append(inputitem);
            return inputitem;
        },
        
        _addNumericPasswordField: function(name, label, required) {
            var labelitem = $("<label for='" + name + "'>" + label + "</label>");
            var inputitem = $("<input type='text' onkeypress='return numbersonly(event)' class='medium' id='" + name + "' name='" + name + "' />");
            if (required) {
                labelitem.addClass('required');
                inputitem.addClass('required');
            }
            this._content.append(labelitem);
            this._content.append(inputitem);
            return inputitem;
        },

        _addCheckboxField: function(name, label, required) {
            var labelitem = $("<label for='" + name + "'>" + label + "</label>");
            var inputitem = $("<input type='checkbox' class='medium' id='" + name + "' name='" + name + "' />");
            if (required) {
                labelitem.addClass('required');
                inputitem.addClass('required');
            }
            this._content.append(labelitem);
            this._content.append(inputitem);
            return inputitem;
        },
        
        _addSelectField: function(name, label, required, initial, options) {
            var labelitem = $("<label for='" + name + "'>" + label + "</label>");
            var inputitem = $("<select class='medium' id='" + name + "' name='" + name + "'></select>");
            if (required) {
                labelitem.addClass('required');
                inputitem.addClass('required');
            }
            if (initial) {
                inputitem.append("<option value='" + initial.value + "'>" + initial.label + "</option>");
            }
            if (options) {
                jQuery.each(options, function(index, option) {
                    inputitem.append("<option value='" + option.value + "'>" + option.label + "</option>");
                });                
            }
            this._content.append(labelitem);
            this._content.append(inputitem);
            return inputitem;
        },
        
        _addSelectIpodField: function(name, label, required, initial, options) {
            var labelitem = $("<label for='" + name + "'>" + label + "</label>");
            var inputitem = $("<input type='hidden' class='medium' id='" + name + "' name='" + name + "' value='" + initial.value + "' />");
            if (required) {
                labelitem.addClass('required');
            }
            this._content.append(labelitem);
            this._content.append(inputitem);
            var button = $("<a tabindex='0' href='#" + name + "_list' class='fg-button' id='" + name + "_button'><div class='" + initial.icon + "'>" + initial.label + "</div></a>");
            if (required) {
                button.addClass('required');
            }
            this._content.append(button);
            var list = $("<div id='" + name + "_list'></div>");
            list.hide();
            if (options) {
                var ul = $("<ul></ul>");
                jQuery.each(options, function(index, option) {
                    var li = $("<li></li>");
                    li.append("<a href='#' value='" + option.value + "' valuetxt='" + option.label + "' valueicon='" + option.icon + "'><div class='icon16-text " + option.icon + "'>" + option.label + "</div></a>");
                    if(option.submenu) {
                        var subul = $("<ul></ul>");
                        jQuery.each(option.submenu, function(index, suboption) {
                            subul.append("<li><a href='#' value='" + suboption.value + "' valuetxt='" + option.label + "." + suboption.label + "' valueicon='" + option.icon + "'>" + suboption.label + "</a></li>");
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
                crumbDefaultText: 'Choose a technologie:',
                resultValueField: '#' + name,
                resultTextElement: "#" + name + "_button"
            });
            return inputitem;
        },
        
        _clearTips: function() {
            var self = this, o = this.options;
            $("#" + o.tipsid + " li").remove();
        },
        
        _addTips: function(text) {
            var self = this, o = this.options;
            $("#" + o.tipsid).append("<li>" + text + "</li>");            
        },
        
        _valid: function() {
            var self = this, o = this.options;
            self._clearTips();
            var valid = true;
            jQuery.each(o.fields, function(index, value) {
                if (value.required || self._hasvalue(value)) {
                    switch(value.type) {
                    case 'text':
                        if (!self._validTextLength(value.name, value.option.min, value.option.max)) {
                            $("#" + value.name).addClass('state-error');
                            valid &= self._addTips(value.label + " length has to be between " + value.option. min + " and " + value.option.max + ".");
                        } else {
                            $("#" + value.name).removeClass('state-error');                            
                        }
                        break;
                    case 'numericpassword':
                        if (!self._validTextLength(value.name, value.option.min, value.option.max)) {
                            $("#" + value.name).addClass('state-error');
                            valid &= self._addTips(value.label + " length has to be between " + value.option. min + " and " + value.option.max + ".");
                        } else {
                            $("#" + value.name).removeClass('state-error');                            
                        }
                        break;
                    case 'select':
                    case 'selectipod':
                        if (!self._validNotInitial(value.name, value.option.initial)) {
                            $("#" + value.name + "_button").addClass('state-error');
                            valid &= self._addTips(value.label + " is not selected");
                        } else {
                            $("#" + value.name + "_button").removeClass('state-error');                            
                        }
                        break;
                    }
                }
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
        
        _hasvalue: function(value) {
            var result = false;
            switch(value.type) {
            case 'text':
            case 'numericpassword':
            case 'select':
            case 'selectipod':
                result = ($('#' + value.name).val()).lenght > 0;
                break;
            case 'checkbox':
                result = true;
                break;
            }
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
                        var decoded = '';
                        if (ops.values[value.name]) decoded = $("<div/>").html(ops.values[value.name]).text();
                        $('#' + value.name).val(decoded);
                        break;
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
                        var valueicon = $('#' + value.name + "_list a[value = '" + ops.values[value.name] + "']").attr('valueicon');
                        $('#' + value.name + '_button').html("<div class='" + valueicon + "'>" + valuetxt + "<div>");
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
})(jQuery);