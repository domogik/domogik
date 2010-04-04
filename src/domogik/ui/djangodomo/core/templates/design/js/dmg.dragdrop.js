(function($) {
    $.widget("ui.dragdrop", {
        previous_idZone : null,
        current_element : null,
        
        _init: function() {
            var self = this, o = this.options;
        	$("ul.draggables", this.element).each(function() {
                var zone = $(this);
                var idZone = "target_" + zone.attr('value');        
                zone.attr('id', idZone);
                zone.attr('aria-labelledby', idZone + '_header');
                zone.attr('role', 'list');
                zone.prev(o.choice).attr('id', idZone + '_header');
                $("li.draggable", this).each(function() {
                    var element = $(this);
        
                    // Set initial values so can be moved
                    element.css('top', '0px');
                    element.css('left', '0px');
        
                    // Put the list items into the keyboard tab order
                    element.attr('tabIndex', '0');
               
                    // Set ARIA attributes for elements
                    element.attr('aria-grabbed', 'false');
                    element.attr('aria-haspopup', 'true');
                    element.attr('role', 'listitem');
                       
                    // Add event handlers
                    self._initialise(this);
                });
            });
        },
    
        cancel: function() {
            this._moveObject(this.current_element, this.previous_idZone);
            this.current_element = null;
            this.previous_idZone = null;
        },
        
        valid: function() {
            this.current_element = null;
            this.previous_idZone = null;
        },
        
        _initialise : function(objNode) {
            var main = this;
            // Add event handlers
            objNode.onmousedown = function(e) { main._dragStart(e, objNode);return false;};
            objNode.onclick = function() {this.focus();};
            objNode.onkeydown = function(e) { main._keyboardDragDrop(e, objNode);};
            document.body.onclick = main._removePopup;
        },
    
        _dragStart : function(objEvent, objNode) {
            var main = this;
            objEvent = objEvent || window.event;
            var idFrom = objNode.parentNode.getAttribute('id');

            this.previous_idZone = idFrom;
            this.current_element = objNode;

            this._removePopup();

            // Initialise properties
            objNode.lastX = objEvent.clientX;
            objNode.lastY = objEvent.clientY;
            objNode.style.zIndex = '2';
            objNode.setAttribute('aria-grabbed', 'true');
            
            $(main.objCurrent).addClass('dragged');
            
            document.onmousemove = function(e) { main._dragMove(e, objNode);return false;};
            document.onmouseup = function(e) { main._dragEnd(e, objNode);return false;};
            this._showTargets(idFrom);
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
            var main = this;
            var idFrom = objNode.parentNode.getAttribute('id');
            var iPosition = calculatePosition(objNode);

            var idTarget = main._getTarget(iPosition, idFrom);
    
            main._dropObject(objNode, idTarget);
    
            document.onmousemove = null;
            document.onmouseup   = null;
            main.objCurrent = null;
        },
        
        _showTargets : function (idFrom) {
            // Highlight the targets for the current drag item
            $('ul.draggables[id!='+idFrom+']').each(function(i) {
                    $(this).parent()
                        .addClass('highlight')
                        .attr('aria-dropeffect', 'move');
            });
        },

        _hideTargets : function () {
            // Highlight the targets for the current drag item
            $("ul.draggables").each(function(i) {
                $(this).parent()
                    .removeClass('highlight')
                    .removeAttr('aria-dropeffect');
            });
        },
        
        _getTarget : function(iPosition, idFrom) {
            var iTolerance = 40;
            var iLeft, iRight, iTop, iBottom;
            var res ='';
        
            $('ul.draggables[id!='+idFrom+']').each(function(i) {
                var zPosition = calculatePosition(this);
                // Get position of the list
                iLeft = zPosition.offsetLeft - iTolerance;
                iRight = iLeft + this.offsetWidth + iTolerance;
                iTop = zPosition.offsetTop - iTolerance;
                iBottom = iTop + this.offsetHeight + iTolerance;
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
    
        _dropObject : function(objNode, idTarget) {
            this._removePopup();
            this._moveObject(objNode, idTarget);
            this._hideTargets();
            this._reset(objNode);
        },
        
        _moveObject : function(objNode, idTarget) {
            if (idTarget.length > 0) {
                var element = $(objNode).detach();
                var target = $('#' + idTarget).append(element);
                this._initialise(objNode);
    
                // Remove empty node if there are artists in list
                $('li.empty', target).remove();
    
                $('ul.draggables:not(:has(li))').html("<li class='empty'>Empty</li>");
                var element_value = element.attr('value');
                var target_value = target.attr('value');
                if(this.options.dropcallback) this.options.dropcallback(this, element_value, target_value);
            } else {
                this.valid();
            }
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
            var main = this, o = this.options;

            objEvent = objEvent || window.event;
            var iKey = objEvent.keyCode;
    
            var idFrom = objNode.parentNode.getAttribute('id');
            
            if (iKey == 32) { // Space
                document.onkeydown = function(){return objEvent.keyCode==38 || objEvent.keyCode==40 ? false : true;};
                // Set ARIA properties
                objNode.setAttribute('aria-grabbed', 'true');
                objNode.setAttribute('aria-owns', 'popup');
                
                // Build context menu
                var objMenu = $("<ul id='popup' role='menu'></ul>");
                
                $('ul.draggables[id!='+idFrom+']').each(function(i) {
                    var self = this;
                    var objChoice = $("<li>" + $(this).prev(o.choice).text() + "</li>")
                    objChoice.attr('tabIndex', -1);
                    objChoice.attr('role', 'menuitem');
                    objChoice.mousedown(function(e) {main._dropObject(objNode, self.id); return false;});
                    objChoice.keydown(function(e) {main._handleContext(e, objNode, self.id)});
                    objMenu.append(objChoice);
                });
            
                $(objNode).append(objMenu);
                objMenu.find(":first").focus();
                main._showTargets(idFrom);
            }
        },
    
        _removePopup : function() {
            document.onkeydown = null;
            $('#popup').remove();
        },
    
        _handleContext : function(objEvent, objNode, idTarget) {
            var main = this;
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
                    main._dropObject(objNode, idTarget);
                    break;
                case 27 : // Escape
                case 9  : // Tab
                    this._removePopup();
                    this._reset(objNode);
                    this._hideTargets();
                    break;
            }
        }
    
    });
    
    $.extend($.ui.dragdrop, {
        defaults: {
            choice: ".choice",
            dropcallback: null
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