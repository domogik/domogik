const close_without_change = 10000; // 10 seconds
const close_with_change = 3000; // 3 seconds
const state_reset_status = 4000; // 4 seconds

(function($) {
    /* Mini Widget */
    $.ui.widget_core.subclass("ui.widget_1x1_extended", {
        // default options
        options: {
            isOpenable: true,
            hasAction: true,
            hasStatus: true,
            namePosition: 'nametopleft'
        },

        widget: function(params) {
            this._super(params);
            var self = this, o = this.options, p = this.params;
            this.isOpen = false;
            this.element.addClass("widget_1x1_extended")
                .addClass("icon32-usage-" + params.usage)
                .processing();
            this._elementValue =  $("<div class='widget_value'></div>");
            this.element.append(this._elementValue);

            if (o.isOpenable) {
                this._elementBlur = $("<div class='blur'></div>");
                this.element.append(this._elementBlur);
                this.element.blur(function () {self.close();});                
                this._elementClose = this._addButtonIcon("widget_close", "left", "icon32-action-cancel", function (e) {self.close();e.stopPropagation();});
                this._elementName = $("<span class='name " + o.namePosition + "'>" + p.devicename + "<br/>" + p.featurename + "</span>");
                this.element.append(this._elementName);
                this.element.addClass('clickable');
                this.element.click(function (e) {self._onclick();e.stopPropagation();})
                    .keypress(function (e) {if (e.which == 13 || e.which == 32) {self._onclick(); e.stopPropagation();}
                              else if (e.keyCode == 27) {self.close(); e.stopPropagation();}});
            } else {
                if (o.hasAction) {
                    this.element.addClass('clickable');
                    this.element.click(function (e) {self.action();e.stopPropagation();})
                        .keypress(function (e) {if (e.which == 13 || e.which == 32) {self._action; e.stopPropagation();}});                    
                }
            }
            if(o.hasStatus) {
                this._elementStatus = $("<div class='status'></div>");
                this.element.append(this._elementStatus);                
            }
        },

        _onclick: function() {
            var self = this, o = this.options;
            if (o.isOpenable) {
                if (this.isOpen) {
                    this.close();
                } else {
                    this.open();
                }
            }
        },

        _open: function() {
            var self = this, o = this.options;
            if (!this.isOpen) {
                // Close all openned widgets
//                $('.widget_mini').widget_mini_core('close');
                this.isOpen = true;
                this.element.removeClass('closed')
                    .addClass('opened');    
                this.element.doTimeout( 'timeout', close_without_change, function(){
                    self.close();
                });
            }
        },
        
        _close: function() {
            if (this.isOpen) {
                this.isOpen = false;
                this.element.removeClass('opened')
                    .addClass('closed');                
            }
            this.element.doTimeout( 'timeout');
        },

        open: function() {
            this._open();
        },
            
        close: function() {
                this._close();
        },
        
        _addButtonIcon: function(css, position, icon, action) {
            var element = $("<div class='widget_button_icon " + css + " " + position + " " + icon + "'></div>")
                .click(action);
            this.element.append(element);
            return element;
        },

        _addButtonText: function(css, position, icon, text, action) {
            var element = $("<div class='widget_button_text " + css + " " + position + " " + icon + "'>" + text + "</div>")
                .click(action);
            this.element.append(element);
            return element;
        },

        cancel: function() {
            var self = this, o = this.options;
            this._stopProcessingState();
            this._displayStatusError();
        },

        /* Valid the processing state */
        valid: function(confirmed) {
            var self = this, o = this.options;
            this._stopProcessingState();
            if (confirmed) {
                this._displayStatusOk();
                this.element.doTimeout( 'resetStatus', state_reset_status, function(){
                    self._displayResetStatus();
                });
            } else {
                self._displayResetStatus();                
            }
        },

        _displayIcon: function(icon) {
            if (this.previousIcon) {
                this.element.removeClass(this.previousIcon);
            }
            this.previousIcon = icon;
            this.element.addClass(icon);
        },

        _startProcessingState: function() {
            this.element.processing('start');
        },

        _stopProcessingState: function() {
            this.element.processing('stop');
        },

        /* Status */
        _writeStatus: function(text) {
            var self = this, o = this.options;
            if(o.hasStatus) {
                this._elementStatus.text(text);
            }
        },

        _displayStatusError: function() {
            var self = this, o = this.options;
            if(o.hasStatus) {
                this._elementStatus.removeClass('ok');
                this._elementStatus.addClass('error');
            }
        },

        _displayStatusOk: function() {
            var self = this, o = this.options;
            if(o.hasStatus) {
                this._elementStatus.addClass('ok');
                this._elementStatus.removeClass('error');
            }
        },

        _displayResetStatus: function() {
            var self = this, o = this.options;
            if(o.hasStatus) {
                this._elementStatus.removeClass('ok');
                this._elementStatus.removeClass('error');
            }
        }
    });
})(jQuery);