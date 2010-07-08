(function($) {
    $.ui.widget.subclass('ui.subdraggable', $.ui.draggable.prototype)
    $.ui.subdraggable.subclass("ui.dmg_draggable", {
        // default options
        options: {
        },

        _init:function() {
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
        }
    });
})(jQuery);
