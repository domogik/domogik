(function($) {
    $.ui.dragdrop_core.subclass("ui.dragdrop_widgets", {
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
            var from_id = $(objNode).attr('ddfromid');
            this._showTargets(from_id);
        },
        
        _showTargets : function (from_id) {
            // Highlight the targets for the current drag item
            $.each(this.zones, function() {
                if (this.id != from_id) {
                    this.element.addClass('highlight')
                        .attr('aria-dropeffect', 'move');
                }
            });
        },

        _hideTargets : function () {
            // Highlight the targets for the current drag item
            $.each(this.zones, function() {
                this.element.removeClass('highlight')
                    .removeAttr('aria-dropeffect');
            });
        },
        
        _dropObject : function(objNode, target_id) {
            this._hideTargets();
            this._moveObject(objNode, target_id, true);
            this._super(objNode, target_id);
        },
        
        _moveObject : function(objNode, target_id, runcallback) {
            var self = this, o = this.options;
            // Get from zone
            var from_id = $(objNode).attr('ddfromid');
            
            if (target_id.length > 0 && from_id != target_id) { // If we are above a target
                // Get item
                var item_value = $(objNode).attr('ddvalue');
                var item = $(objNode).detach();

                // Get target zone
                var zone_target = this._getZone(target_id);
                this.current_zone = zone_target;
                zone_target.list.append(item);
                var target_value = zone_target.element.attr('ddvalue');

                this._initialise(objNode);

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
