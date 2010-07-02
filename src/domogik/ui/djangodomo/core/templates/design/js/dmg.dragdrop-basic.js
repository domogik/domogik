(function($) {
    $.ui.dragdrop_core.subclass("ui.dragdrop_basic", {
        // default options
        options: {
        },

        current_item : null,
        current_zone : null,

        _init:function() {
            var self = this, o = this.options;
        },
        
        cancel: function() {
            var zone_from_id = $(this.current_item).attr('ddfromid');
            var current_zone_id = $(this.current_zone).attr('id');
            $(this.current_item).attr('ddfromid', current_zone_id);
            this._moveObject(this.current_item, zone_from_id, false);
            $(this.current_item).attr('ddfromid', zone_from_id);
            this.current_item = null;
            this.current_zone = null;
        },
        
        valid: function() {
            var current_zone_id = $(this.current_zone).attr('id');
            $(this.current_item).attr('ddfromid', current_zone_id);
            this.current_item = null;
            this.current_zone = null;
        },
        
        _dragInit : function(objNode) {
            this.current_item = objNode;
            this._super(objNode);
        },
        
        _dragStart : function(objEvent, objNode) {
            this._dragInit(objNode);
            this._super(objEvent, objNode);
        },
        
        _dropObject : function(objNode, target_id) {
            this._moveObject(objNode, target_id, true);
            this._super(objNode, target_id);
        },
        
        _moveObject : function(objNode, target_id, runcallback) {
            var self = this, o = this.options;
            if (target_id.length > 0) { // If we are above a target
                // Get item
                var item_value = $(objNode).attr('ddvalue');
                var item = $(objNode).detach();

                // Get target zone
                var zone_target = this._getZone(target_id);
                this.current_zone = zone_target;
                zone_target.list.append(item);
                var target_value = zone_target.element.attr('ddvalue');
                
                // Get from zone
                var from_id = $(objNode).attr('ddfromid');
                var zone_from = this._getZone(from_id);
                
                this._initialise(objNode);
                
                // Remove empty node if there are element in list
                $('li.empty', zone_target.element).remove();
    
                if ($('li', zone_from.list).length == 0) {
                    zone_from.list.html("<li class='empty'><p>Empty</p></li>");
                }
                if (runcallback) {
                    if (zone_target.dropcallback) {
                        zone_target.dropcallback(this, item_value, target_value);
                    } else if (this.options.generaldropcallback) {
                        this.options.generaldropcallback(this, item_value, target_value);                    
                    }                    
                }
            } else {
                this.valid();
            }
        }

    });
})(jQuery);
