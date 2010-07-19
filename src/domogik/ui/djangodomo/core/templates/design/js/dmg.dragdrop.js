(function($) {
    $.ui.widget.subclass('ui.subdraggable', $.ui.draggable.prototype)
    $.ui.subdraggable.subclass("ui.dmg_draggable", {
        // default options
        options: {
        },

        _init:function() {
            var self = this, o = this.options;
            this.element.attr('tabindex', '0');
            this.element.onkeydown = function(e) { self._keyboardDragDrop(e);};
        },
        
        _mouseStop: function(event) {
            //If we are using droppables, inform the manager about the drop
            var dropped = false;
            if ($.ui.ddmanager && !this.options.dropBehaviour)
                dropped = $.ui.ddmanager.drop(this, event);
    
            //if a drop comes from outside (a sortable)
            if(this.dropped) {
                dropped = this.dropped;
                this.dropped = false;
            }
            
            //if the original element is removed, don't bother to continue
            if(!this.element[0] || !this.element[0].parentNode)
                return false;
    
            if(!this.options.waitValidation) {
                if((this.options.revert == "invalid" && !dropped) || (this.options.revert == "valid" && dropped) || this.options.revert === true || ($.isFunction(this.options.revert) && this.options.revert.call(this.element, dropped))) {
                    this.revert(event);
                } else {
                    this.end(event);
                }
            }
            return false;
        },
        
        revert: function(event) {
            var self = this;
            $(this.helper).animate(this.originalPosition, parseInt(this.options.revertDuration, 10), function() {
                self.end(event);
            });
        },
        
        end: function(event) {
            this.options.waitValidation = false;
            if(this._trigger("stop", event) !== false) {
                this._clear();
            }            
            this.options.waitValidation = false;
        },
        
        _keyboardDragDrop : function(objEvent) {
            var self = this, o = this.options;

            objEvent = objEvent || window.event;
            var iKey = objEvent.keyCode;
    
//            var from_id = $(objNode).attr('ddfromid');
            
            if (iKey == 32) { // Space
                document.onkeydown = function(){return objEvent.keyCode==38 || objEvent.keyCode==40 ? false : true;};
                // Set ARIA properties
                this.setAttribute('aria-grabbed', 'true');
                this.setAttribute('aria-owns', 'popup');
                
                // Build context menu
                var objMenu = $("<ul id='popup' role='menu'></ul>");
/*                $.each(this.zones, function() {
                    var zone = this;
//                    if (this.id != from_id) {
                        var name = this.name
                        var objChoice = $("<li>" + name + "</li>")
                        objChoice.attr('tabIndex', -1);
                        objChoice.attr('role', 'menuitem');
                        objChoice.mousedown(function(e) {self._dropObject(objNode, zone.id); return false;});
                        objChoice.keydown(function(e) {self._handleContext(e, objNode, zone.id)});
                        objMenu.append(objChoice);
//                    }
                });
*/            
                this.append(objMenu);
                objMenu.find(":first").focus();
//                self._showTargets(from_id);
            }
        }
    });
})(jQuery);
