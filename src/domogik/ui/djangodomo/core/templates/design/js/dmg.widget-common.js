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
            this._identity = $("<canvas class='identity' width='60' height='60'></canvas>")
            this.element.append(this._identity);
            this._elementBlur = $("<div class='blur'></div>");
            this.element.append(this._elementBlur);
            this._elementName = $("<span class='name " + o.nameposition + "'>" + o.devicename + "<br/>" + o.featurename + "</span>");
            this.element.append(this._elementName);
            this._elementStatus = $("<div class='status'></div>");
            this.element.append(this._elementStatus);
            this._elementClose = this._addButtonIcon("widget_close", "left", "icon32-action-cancel", function (e) {self.close();e.stopPropagation();});
            this.element.keypress(function (e) {
					switch(e.keyCode) { 
					case 27: // Esc
						self.close();
						break;
					}
					e.stopPropagation();
				});
            this.element.blur(function () {self.close();});
            
            var canvas = this._identity.get(0);
            if (canvas.getContext){
                var ctx = canvas.getContext('2d');
                ctx.beginPath();
                ctx.font = "6pt Arial";
                ctx.textBaseline = "top"
                ctx.fillText(o.devicename, 15, 5);
                ctx.translate(5,60);
                ctx.rotate(-(Math.PI/2));
                ctx.fillText(o.featurename, 0, 0);  
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