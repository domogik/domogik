(function($) {
    $.ui.widget.subclass("ui.dragdrop_core", {
        // default options
        options: {
            zonesselector: ".targetdrop",
            listselector: ".draggables",
            itemselector: ".draggable",
            labelselector: "legend",
            dragcopy: false
        },

        _init:function() {
            var self = this, o = this.options;
            this.zones = new Array;
            // Find all zones
            $.each(o.zones, function(index, value) {
                $(value.zonesselector, self.element).each(function() {
                    var zone = new Object;
                    zone.element = $(this);
                    zone.dom = this;
                    
                    // Save zone options
                    zone.zonesselector = value.zonesselector;
                    zone.itemselector = value.itemselector;
                    zone.listselector = value.listselector;
                    zone.labelselector = value.labelselector;
                    zone.dragcopy = value.dragcopy;

                    // Set zone id
                    zone.id = zone.element.attr('id');
                    zone.value = zone.element.attr('ddvalue'); 
                    zone.name = zone.element.attr('ddname');
                    if (!zone.id || zone.id == '') {
                        zone.id = "target_" + zone.value;        
                        zone.element.attr('id', zone.id);                        
                    }

                    // Set choice label
                    var choice = zone.element.children(zone.labelselector + ":first");
                    choice.attr('id', zone.id + '_header');

                    zone.dropcallback = value.dropcallback;
                    
                    // Find zone list
                    zone.list = zone.element.children(zone.listselector + ":first");
                    zone.list.addClass('draggables')
                        .attr('role', 'list')
                        .attr('aria-labelledby', zone.id + '_header');

                    self.zones.push(zone); // Add the zone to the list
    
                    $("li" + zone.itemselector, zone.list).each(function() {
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
                        
                        element.attr('ddfromid', zone.id);
                        
                        // Add event handlers
                        self._initialise(this);
                    });                    
                });

            });
        },

        updatezone: function(selector) {
            var self = this, o = this.options;
            $.each(this.zones, function(index, zone) {
                if (zone.zonesselector == selector) {
                    zone.value = zone.element.attr('ddvalue');
                    zone.name = zone.element.attr('ddname');

                    // Find zone list
                    zone.list = zone.element.children(zone.listselector + ":first");
    
                    $("li" + zone.itemselector, zone.list).each(function() {
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

                        element.attr('ddfromid', zone.id);

                        // Add event handlers
                        self._initialise(this);
                    });                    
                }
            });
        },
        
        _initialise : function(objNode) {
            var self = this;
            // Add event handlers
            objNode.onmousedown = function(e) { self._dragStart(e, objNode);return false;};
            objNode.onclick = function() {this.focus();};
            objNode.onkeydown = function(e) { self._keyboardDragDrop(e, objNode);};
            document.body.onclick = self._removePopup;
        },
    
        _dragInit : function(objNode) {
        },
        
        _dragStart : function(objEvent, objNode) {
            var self = this, o = this.options;
            objEvent = objEvent || window.event;

            this._removePopup();

            // Initialise properties
            objNode.lastX = objEvent.clientX;
            objNode.lastY = objEvent.clientY;
            objNode.style.zIndex = '2';
            objNode.setAttribute('aria-grabbed', 'true');
            
            $(self.objCurrent).addClass('dragged');
            
            document.onmousemove = function(e) { self._dragMove(e, objNode);return false;};
            document.onmouseup = function(e) { self._dragEnd(e, objNode);return false;};
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

            var position = calculatePosition(objNode);

            var target_id = self._getTarget(position);
    
            self._dropObject(objNode, target_id);
    
            document.onmousemove = null;
            document.onmouseup   = null;
            self.objCurrent = null;
        },
        
        _getZone : function (id) {
            var ret = null
            $.each(this.zones, function() {
                if (this.id == id) ret = this;
            });
            return ret;
        },
        
        _getTarget : function(iPosition) {
            var iTolerance = 40;
            var iLeft, iRight, iTop, iBottom;
            var res ='';

            $.each(this.zones, function() {
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
            });

            // Current object is not over a target
            return res;
        },
    
        _dropObject : function(objNode, target_id) {
            this._removePopup();
            this._reset(objNode);
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
    
            var from_id = $(objNode).attr('ddfromid');
            
            if (iKey == 32) { // Space
                document.onkeydown = function(){return objEvent.keyCode==38 || objEvent.keyCode==40 ? false : true;};
                // Set ARIA properties
                objNode.setAttribute('aria-grabbed', 'true');
                objNode.setAttribute('aria-owns', 'popup');
                
                // Build context menu
                var objMenu = $("<ul id='popup' role='menu'></ul>");
                $.each(this.zones, function() {
                    var zone = this;
                    if (this.id != from_id) {
                        var name = this.name
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
                self._showTargets(from_id);
            }
        },
    
        _removePopup : function() {
            document.onkeydown = null;
            $('#popup').remove();
        },
    
        _handleContext : function(objEvent, objNode, target_id) {
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
                    self._dragInit(objNode);
                    self._dropObject(objNode, target_id);
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