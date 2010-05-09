(function($) {
    $.widget("ui.dragdrop", {
        previous_idZone : null,
        current_element : null,
        _init:function() {
            var self = this, o = this.options;
            this.zones = new Array;
        },

        addzones: function(parameters) {
            var self = this, o = this.options;
            $(parameters.id).find(o.target).each(function() {
                var zone = new Object;
                var element = $(this);
                var idZone = "target_" + element.attr('value');        
                element.attr('id', idZone);
                var choice = element.children(o.choice + ":first");
                choice.attr('id', idZone + '_header');
                zone.name = choice.text();
                zone.id = idZone;
                zone.element = element;
                zone.dom = this;
                zone.drag = parameters.drag;
                zone.drop = parameters.drop;
                zone.droporigin = parameters.droporigin;
                zone.keeptrace = parameters.keeptrace;
                zone.dropcallback = parameters.dropcallback;
                zone.list = element.children("ul:first");
                self.zones.push(zone); // Add the zone to the list
                
                zone.list.attr('role', 'list')
                    .attr('aria-labelledby', zone.id + '_header');

                if ($("li.draggable, li.trace", zone.list).length > 0) {
                    $("li.draggable", zone.list).each(function() {
                        var element = $(this);
                        element.addClass('draggable');
                        
                        // Set initial values so can be moved
                        element.css('top', '0px');
                        element.css('left', '0px');
            
                        // Put the list items into the keyboard tab order
                        element.attr('tabIndex', '0');
                   
                        // Set ARIA attributes for elements
                        element.attr('aria-grabbed', 'false');
                        element.attr('aria-haspopup', 'true');
                        element.attr('role', 'listitem');

                        //element.attr('zoneorigin', zone.id);

                        // Add event handlers
                        self._initialise(this);
                    });                    
                } else {
                    zone.list.append("<li class='empty'><p>Empty</p></li>");
                }
            });
        },
    
        cancel: function() {
            this._moveObject(this.current_element, this.previous_idZone, false);
            this.current_element = null;
            this.previous_idZone = null;
        },
        
        valid: function() {
            this.current_element = null;
            this.previous_idZone = null;
        },
        
        _initialise : function(objNode) {
            var self = this;
            // Add event handlers
            objNode.onmousedown = function(e) { self._dragStart(e, objNode);return false;};
            objNode.onclick = function() {this.focus();};
            objNode.onkeydown = function(e) { self._keyboardDragDrop(e, objNode);};
            document.body.onclick = self._removePopup;
        },
    
        _dragStart : function(objEvent, objNode) {
            var self = this, o = this.options;
            objEvent = objEvent || window.event;
            var zoneFrom = $(objNode).parents(o.target + ":first");
            var idOrigin = $(objNode).attr('zoneorigin');
            var idFrom = zoneFrom.attr('id');
            this.current_element = objNode;

            this._removePopup();

            // Initialise properties
            objNode.lastX = objEvent.clientX;
            objNode.lastY = objEvent.clientY;
            objNode.style.zIndex = '2';
            objNode.setAttribute('aria-grabbed', 'true');
            
            $(self.objCurrent).addClass('dragged');
            
            document.onmousemove = function(e) { self._dragMove(e, objNode);return false;};
            document.onmouseup = function(e) { self._dragEnd(e, objNode);return false;};
            this._showTargets(idFrom, idOrigin);
        },
    
        _dragMove : function(objEvent, objNode) {
            objEvent = objEvent || window.event;
    
            // Calculate new position
            var iCurrentY = objEvent.clientY;
            var iCurrentX = objEvent.clientX;
            var iYPos = parseInt(objNode.style.top, 10);
            var iXPos = parseInt(objNode.style.left, 10);
            var iNewX, iNewY;
    
            iNewX = iXPos + iCurrentX - objNode.lastX;
            iNewY = iYPos + iCurrentY - objNode.lastY;
    
            objNode.style.left = iNewX + 'px';
            objNode.style.top = iNewY + 'px';
            objNode.lastX = iCurrentX;
            objNode.lastY = iCurrentY;
        },
    
        _dragEnd : function(objEvent, objNode) {
            var self = this, o = this.options;
            var zoneFrom = $(objNode).parents(o.target + ":first");
            var idFrom = zoneFrom.attr('id');

            var iPosition = calculatePosition(objNode);
            var idOrigin = $(objNode).attr('zoneorigin');

            var idTarget = self._getTarget(iPosition, idFrom, idOrigin);
    
            self._dropObject(objNode, idTarget);
    
            document.onmousemove = null;
            document.onmouseup   = null;
            self.objCurrent = null;
        },
        
        _showTargets : function (idFrom, idOrigin) {
            // Highlight the targets for the current drag item
            $.each(this.zones, function() {
                if (this.id != idFrom && (this.drop || (this.droporigin && this.id == idOrigin))) {
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
        
        _getZone : function (id) {
            var ret = null
            $.each(this.zones, function() {
                if (this.id == id) ret = this;
            });
            return ret;
        },
        
        _getTarget : function(iPosition, idFrom, idOrigin) {
            var iTolerance = 40;
            var iLeft, iRight, iTop, iBottom;
            var res ='';

            $.each(this.zones, function() {
                if (this.id != idFrom && (this.drop || (this.droporigin && this.id == idOrigin))) {
                    var zPosition = calculatePosition(this.dom);
                    // Get position of the list
                    iLeft = zPosition.offsetLeft - iTolerance;
                    iRight = iLeft + this.dom.offsetWidth + iTolerance;
                    iTop = zPosition.offsetTop - iTolerance;
                    iBottom = iTop + this.dom.offsetHeight + iTolerance;
                    // Determine if current object is over the target
                    if (iPosition.offsetLeft > iLeft && iPosition.offsetLeft < iRight && iPosition.offsetTop > iTop && iPosition.offsetTop < iBottom)
                    {
                        res = this.id;
                        return false;
                    }
                }
            });

            // Current object is not over a target
            return res;
        },
    
        _dropObject : function(objNode, idTarget) {
            this._removePopup();
            this._moveObject(objNode, idTarget, true);
            this._hideTargets();
            this._reset(objNode);
        },
        
        _moveObject : function(objNode, idTarget, runcallback) {
            var self = this, o = this.options;
            if (idTarget.length > 0) {
                var element_value = objNode.getAttribute('value');
                var element_origin = objNode.getAttribute('zoneorigin');
                var zone_origin = this._getZone(element_origin);
                var zone_target = this._getZone(idTarget);
                var zoneFrom = $(objNode).parents(o.target + ":first");
                var idFrom = zoneFrom.attr('id');
                this.previous_idZone = idFrom;
                var zone_from = this._getZone(idFrom);
                if (zone_origin && zone_origin.keeptrace) {
                    $("#"+element_value+"_trace",zone_origin.element).remove();
                    if (idTarget != element_origin) { // If we are back to the original zone
                        var text = null;
                        if (o.featurename) {
                            text = $(o.featurename, objNode).html();
                        } else {
                            text = $(objNode).text() 
                        }
                        text += "<br />Associated with " + zone_target.name;                  
                        zone_origin.list.append("<li id='" + element_value + "_trace' class='trace'>" + text + "</li>");
                    }
                }
                var element = $(objNode).detach();
                zone_target.list.append(element);                    
                var target_value = zone_target.element.attr('value');
                this._initialise(objNode);
                
                // Remove empty node if there are element in list
                $('li.empty', zone_target.element).remove();
    
                if ($('li', zone_from.list).length == 0) {
                    zone_from.list.html("<li class='empty'><p>Empty</p></li>");
                }
                if (runcallback) {
                    if (zone_target.dropcallback) {
                        zone_target.dropcallback(this, element_value, target_value);
                    } else if (this.options.generaldropcallback) {
                        this.options.generaldropcallback(this, element_value, target_value);                    
                    }                    
                }
            } else {
                this.valid();
            }
        },
        
        _dropcallback: function() {
            
        },
        
        _reset: function(objNode) {
            // Reset properties
            objNode.style.left = '0px';
            objNode.style.top = '0px';
    
            objNode.style.zIndex = 'auto';
            objNode.setAttribute('aria-grabbed', 'false');
            objNode.removeAttribute('aria-owns');
            $(objNode).removeClass('dragged');
        },
        
        _keyboardDragDrop : function(objEvent, objNode) {
            var self = this, o = this.options;

            objEvent = objEvent || window.event;
            var iKey = objEvent.keyCode;
    
            var zoneFrom = $(objNode).parents(o.target + ":first");
            var idFrom = zoneFrom.attr('id');
            var idOrigin = $(objNode).attr('zoneorigin');
            
            if (iKey == 32) { // Space
                document.onkeydown = function(){return objEvent.keyCode==38 || objEvent.keyCode==40 ? false : true;};
                // Set ARIA properties
                objNode.setAttribute('aria-grabbed', 'true');
                objNode.setAttribute('aria-owns', 'popup');
                
                // Build context menu
                var objMenu = $("<ul id='popup' role='menu'></ul>");
                $.each(this.zones, function() {
                    var zone = this;
                    if (this.id != idFrom && (this.drop || (this.droporigin && this.id == idOrigin))) {
                        var name = this.name
                        if (this.id == idOrigin) {
                            name = "Remove association";                            
                        }
                        var objChoice = $("<li>" + name + "</li>")
                        objChoice.attr('tabIndex', -1);
                        objChoice.attr('role', 'menuitem');
                        objChoice.mousedown(function(e) {self._dropObject(objNode, zone.id); return false;});
                        objChoice.keydown(function(e) {self._handleContext(e, objNode, zone.id)});
                        objMenu.append(objChoice);
                    }
                });
            
                $(objNode).append(objMenu);
                objMenu.find(":first").focus();
                self._showTargets(idFrom);
            }
        },
    
        _removePopup : function() {
            document.onkeydown = null;
            $('#popup').remove();
        },
    
        _handleContext : function(objEvent, objNode, idTarget) {
            var self = this;
            objEvent = objEvent || window.event;
            var objItem = objEvent.target || objEvent.srcElement;
            var iKey = objEvent.keyCode;
            var objFocus, objList, strTarget, iCounter;
    
            // Cancel default behaviour
            if (objEvent.stopPropagation)
            {
                objEvent.stopPropagation();
            }
            else if (objEvent.cancelBubble)
            {
                objEvent.cancelBubble = true;
            }
            if (objEvent.preventDefault)
            {
                objEvent.preventDefault();
            }
            else if (objEvent.returnValue)
            {
                objEvent.returnValue = false;
            }
    
            switch (iKey)
            {
                case 38 : // Up arrow
                   objFocus = objItem.previousSibling;
                   if (!objFocus)
                   {
                       objFocus = objItem.parentNode.lastChild
                   }
                   objFocus.focus();
                   break;
               case 40 : // Down arrow
                   objFocus = objItem.nextSibling;
                   if (!objFocus)
                   {
                       objFocus = objItem.parentNode.firstChild
                   }
                   objFocus.focus();
                   break;
                case 13 : // Enter
                    self.current_element = objNode;
                    self._dropObject(objNode, idTarget);
                    break;
                case 27 : // Escape
                case 9  : // Tab
                    self._removePopup();
                    self._reset(objNode);
                    self._hideTargets();
                    break;
            }
        }
    
    });
    
    $.extend($.ui.dragdrop, {
        defaults: {
            choice: ".choice",
            generaldropcallback: null
        }
    });
})(jQuery);

function calculatePosition (objElement) {
    var offsetTop = 0;
    var offsetLeft = 0;            
    // Get offset position in relation to parent nodes
    if (objElement.offsetParent)
    {
        do 
        {
            offsetTop += objElement['offsetTop'];
            offsetLeft += objElement['offsetLeft'];
            objElement = objElement.offsetParent;
        } while (objElement);
    }
    return {'offsetTop' : offsetTop, 'offsetLeft' : offsetLeft};
}