const close_without_change = 10000; // 10 seconds
const close_with_change = 3000; // 3 seconds
const state_reset_status = 4000; // 4 seconds

(function($) {
    /* Mini Widget */
    $.ui.widget.subclass("ui.widget_mini_core", {
        // default options
        options: {
        },

        _init: function() {
            var self = this, o = this.options;
            this.isOpen = false;
            this.element.addClass('widget_mini')
                .addClass(o.widgettype)
                .addClass("icon32-usage-" + o.usage)
                .attr("tabindex", 0)
                .processing();
            this._elementBlur = $("<div class='blur'></div>");
            this.element.append(this._elementBlur);
            this._elementName = $("<span class='name " + o.nameposition + "'>" + o.devicename + "<br/>" + o.featurename + "</span>");
            this.element.append(this._elementName);
            this._elementStatus = $("<div class='status'></div>");
            this.element.append(this._elementStatus);
            this._elementClose = $("<div class='widget_button widget_close icon32-action-cancel'></div>")
                .click(function (e) {self.close();e.stopPropagation();});
            this.element.append(this._elementClose);
            this.element.keypress(function (e) {
					switch(e.keyCode) { 
					case 27: // Esc
						self.close();
						break;
					}
					e.stopPropagation();
				});

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
        },
        
        open: function() {
            this._open();
		},
		
		close: function() {
            this._close();
		},
        
        runAction: function(data) {
            var self = this, o = this.options;
            if (o.action) {
                this._startProcessingState();
                o.action(this, data);                
            }
        },
        
        cancel: function() {
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
            }
        },
        
        _displayIcon: function(newIcon, previousIcon) {
            if (previousIcon) {
                this.element.removeClass(previousIcon);
            }
            this.element.addClass(newIcon);
        },
        
        _writeStatus: function(text) {
            this._elementStatus.text(text);
        },
        
        _displayStatusError: function() {
            this._elementStatus.addClass('error');
        },
        
        _displayStatusOk: function() {
            this._elementStatus.addClass('ok');
        },
        
        _displayResetStatus: function() {
            this._elementStatus.removeClass('ok');
        },
        
        _startProcessingState: function() {
            this.element.processing('start');
        },
        
        _stopProcessingState: function() {
            this.element.processing('stop');
        }
    });
})(jQuery);