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
            this.element.addClass('widget')
                .addClass(o.widgettype)
                .addClass("icon32-usage-" + o.usage)
                .attr("tabindex", 0)
                .processing();
            this._elementName = $("<span class='name " + o.nameposition + "'>" + o.devicename + "<br/>" + o.featurename + "</span>");
            this._elementName.hide();
            this.element.append(this._elementName);
            this._elementStatus = $("<div class='widget_status'></div>");
            this.element.append(this._elementStatus);
        },
        
        open: function() {
            var self = this, o = this.options;
            this.isOpen = true;
            this._elementBlur = $("<div class='blur'></div>");
            this.element.prepend(this._elementBlur);
            this._elementName.show();
            this.element.removeClass('closed')
				.addClass('opened');    
            this.element.doTimeout( 'timeout', close_without_change, function(){
				self.close();
			});
        },
        
        close: function() {
            this.isOpen = false;
            this._elementBlur.remove();
            this._elementName.hide();
            this.element.removeClass('opened')
				.addClass('closed');
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