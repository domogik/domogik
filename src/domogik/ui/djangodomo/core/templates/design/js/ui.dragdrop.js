// JavaScript Document
// Function to get elements by class name for DOM fragment and tag name
function getElementsByClassName(objElement, strTagName, strClassName)
{
	var objCollection = objElement.getElementsByTagName(strTagName);
	var arReturn = [];
	var strClass, arClass, iClass, iCounter;

	for(iCounter=0; iCounter<objCollection.length; iCounter++)
	{
		strClass = objCollection[iCounter].className;
		if (strClass)
		{
			arClass = strClass.split(' ');
			for (iClass=0; iClass<arClass.length; iClass++)
			{
				if (arClass[iClass] == strClassName)
				{
					arReturn.push(objCollection[iCounter]);
					break;
				}
			}
		}
	}

	objCollection = null;
	return (arReturn);
}

var drag = {
	objCurrent : null,

	initialise : function(objNode)
	{
		// Add event handlers
		objNode.onmousedown = drag.start;
		objNode.onclick = function() {this.focus();};
		objNode.onkeydown = drag.keyboardDragDrop;
		document.body.onclick = drag.removePopup;
	},

	keyboardDragDrop : function(objEvent)
	{
		objEvent = objEvent || window.event;
		drag.objCurrent = this;
		var iKey = objEvent.keyCode;
		var objItem = drag.objCurrent;

			var strExisting = objItem.parentNode.getAttribute('id');
			var objMenu, objChoice;

			if (iKey == 32)
			{
				document.onkeydown = function(){return objEvent.keyCode==38 || objEvent.keyCode==40 ? false : true;};
				// Set ARIA properties
				drag.objCurrent.setAttribute('aria-grabbed', 'true');
				drag.objCurrent.setAttribute('aria-owns', 'popup');
				// Build context menu
				objMenu = document.createElement('ul');
				objMenu.setAttribute('id', 'popup');
				objMenu.setAttribute('role', 'menu');
				
				$('.choice').each(function(i) {
					if (this.id != (strExisting + 'h'))
					{
						objChoice = document.createElement('li');
						objChoice.appendChild(document.createTextNode($('#'+this.id).text()));
						objChoice.tabIndex = -1;
						objChoice.setAttribute('value', (this.id).substr(0, (this.id).length-1));
						objChoice.setAttribute('role', 'menuitem');
						objChoice.onmousedown = function() {drag.dropObject(this.id);};
						objChoice.onkeydown = drag.handleContext;
						objChoice.onmouseover = function() {if (this.className.indexOf('hover') < 0) {this.className += ' hover';} };
						objChoice.onmouseout = function() {this.className = this.className.replace(/\s*hover/, ''); };
						objMenu.appendChild(objChoice);
					}

				});
			
				objItem.appendChild(objMenu);
				objMenu.firstChild.focus();
				objMenu.firstChild.className = 'focus';
				drag.identifyTargets(true);
			}
	},

	removePopup : function()
	{
		document.onkeydown = null;

		var objContext = document.getElementById('popup');

		if (objContext)
		{
			objContext.parentNode.removeChild(objContext);
		}
	},

	handleContext : function(objEvent)
	{
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
               objItem.className = '';
               objFocus.focus();
               objFocus.className = 'focus';
               break;
           case 40 : // Down arrow
               objFocus = objItem.nextSibling;
               if (!objFocus)
               {
                   objFocus = objItem.parentNode.firstChild
               }
               objItem.className = '';
               objFocus.focus();
               objFocus.className = 'focus';
               break;
			case 13 : // Enter
				strTarget = objItem.getAttribute('value');
				drag.dropObject(strTarget);
				break;
			case 27 : // Escape
			case 9  : // Tab
				drag.objCurrent.removeAttribute('aria-owns');
				drag.objCurrent.removeChild(objItem.parentNode);
				drag.objCurrent.focus();
				$("ul.draggables").each(function(i) {
					drag.objCurrent.setAttribute('aria-grabbed', 'false');
					this.removeAttribute('aria-dropeffect');
					this.className = 'draggables';
				});
				break;
		}
	},
	

	start : function(objEvent)
	{
		objEvent = objEvent || window.event;
		drag.removePopup();
		// Initialise properties
		drag.objCurrent = this;

		drag.objCurrent.lastX = objEvent.clientX;
		drag.objCurrent.lastY = objEvent.clientY;
		drag.objCurrent.style.zIndex = '2';
		drag.objCurrent.setAttribute('aria-grabbed', 'true');
		
		drag.objCurrent.className = 'draggable dragged';
		
		document.onmousemove = drag.drag;
		document.onmouseup = drag.end;
		drag.identifyTargets(true);

		return false;
	},

	drag : function(objEvent)
	{
		objEvent = objEvent || window.event;

		// Calculate new position
		var iCurrentY = objEvent.clientY;
		var iCurrentX = objEvent.clientX;
		var iYPos = parseInt(drag.objCurrent.style.top, 10);
		var iXPos = parseInt(drag.objCurrent.style.left, 10);
		var iNewX, iNewY;

		iNewX = iXPos + iCurrentX - drag.objCurrent.lastX;
		iNewY = iYPos + iCurrentY - drag.objCurrent.lastY;

		drag.objCurrent.style.left = iNewX + 'px';
		drag.objCurrent.style.top = iNewY + 'px';
		drag.objCurrent.lastX = iCurrentX;
		drag.objCurrent.lastY = iCurrentY;

		return false;
	},

	calculatePosition : function (objElement, strOffset)
	{
		var iOffset = 0;

		// Get offset position in relation to parent nodes
		if (objElement.offsetParent)
		{
			do 
			{
				iOffset += objElement[strOffset];
				objElement = objElement.offsetParent;
			} while (objElement);
		}

		return iOffset;
	},

	identifyTargets : function (bHighlight)
	{
		var strExisting = drag.objCurrent.parentNode.getAttribute('id');
	
		// Highlight the targets for the current drag item
		$("ul.draggables").each(function(i) {
			if (bHighlight && this.id != strExisting)
			{
				$('#'+this.id).addClass('highlight');
				this.setAttribute('aria-dropeffect', 'move');
			}
			else
			{
				$('#'+this.id).removeClass('highlight');
				this.removeAttribute('aria-dropeffect');
			}
		});
	},

	getTarget : function()
	{
		var strExisting = drag.objCurrent.parentNode.getAttribute('id');
		var iCurrentLeft = drag.calculatePosition(drag.objCurrent, 'offsetLeft');
		var iCurrentTop = drag.calculatePosition(drag.objCurrent, 'offsetTop');
		var iTolerance = 40;
		var iLeft, iRight, iTop, iBottom;
		var res ='';
	
	$("ul.draggables").each(function(i) {
		if (this.id != strExisting)
			{
				// Get position of the list
				iLeft = drag.calculatePosition(this, 'offsetLeft') - iTolerance;
				iRight = iLeft + this.offsetWidth + iTolerance;
				iTop = drag.calculatePosition(this, 'offsetTop') - iTolerance;
				iBottom = iTop + this.offsetHeight + iTolerance;
				// Determine if current object is over the target
				if (iCurrentLeft > iLeft && iCurrentLeft < iRight && iCurrentTop > iTop && iCurrentTop < iBottom)
				{
					res = this.id;
					return false;
				}
			}
		});
		// Current object is not over a target
		return res;
	},

	dropObject : function(strTarget)
	{
		var objClone, objOriginal, objTarget, objEmpty, objBands, objItem;
		drag.removePopup();

		if (strTarget.length > 0)
		{
			// Copy node to new target
			objOriginal = drag.objCurrent.parentNode;
			objClone = drag.objCurrent.cloneNode(true);

			// Remove previous attributes
			objClone.removeAttribute('style');
			objClone.className = objClone.className.replace(/\s*focused/, '');
			objClone.className = objClone.className.replace(/\s*hover/, '');

			// Add focus indicators
			objClone.onfocus = function() {this.className += ' focused'; };
			objClone.onblur = function() {this.className = this.className.replace(/\s*focused/, '');};
			objClone.onmouseover = function() {if (this.className.indexOf('hover') < 0) {this.className += ' hover';} };
			objClone.onmouseout = function() {this.className = this.className.replace(/\s*hover/, ''); };

			objTarget = document.getElementById(strTarget);
			objOriginal.removeChild(drag.objCurrent);
			objTarget.appendChild(objClone);
			drag.objCurrent = objClone;
			drag.initialise(objClone);

			// Remove empty node if there are artists in list
			objEmpty = getElementsByClassName(objTarget, 'li', 'empty');
			if (objEmpty[0])
			{
				objTarget.removeChild(objEmpty[0]);
			}

			// Add an empty node if there are no artists in list
			objBands = objOriginal.getElementsByTagName('li');
			if (objBands.length === 0)
			{
				objItem = document.createElement('li');
				objItem.appendChild(document.createTextNode('Vide'));
				objItem.className = 'empty';
				objOriginal.appendChild(objItem);
			}
		}
				// Reset properties
		drag.objCurrent.style.left = '0px';
		drag.objCurrent.style.top = '0px';

		drag.objCurrent.style.zIndex = 'auto';
		drag.objCurrent.setAttribute('aria-grabbed', 'false');
		drag.objCurrent.removeAttribute('aria-owns');
				drag.objCurrent.className = 'draggable';



		drag.identifyTargets(false);
	},

	end : function()
	{
		var strTarget = drag.getTarget();

		drag.dropObject(strTarget);

		document.onmousemove = null;
		document.onmouseup   = null;
		drag.objCurrent = null;
	}
};

$(function(){
		   
		$("li.draggable").each(function(i) {
										
		 // Set initial values so can be moved
		this.style.top = '0px';
		this.style.left = '0px';

		// Put the list items into the keyboard tab order
		this.tabIndex = 0;

		// Set ARIA attributes for elements
		this.setAttribute('aria-grabbed', 'false');
		this.setAttribute('aria-haspopup', 'true');
		this.setAttribute('role', 'listitem');

		// Provide a focus indicator
		this.onfocus = function() {this.className += ' focused'; };
		this.onblur = function() {this.className = this.className.replace(/\s*focused/, '');};
		this.onmouseover = function() {if (this.className.indexOf('hover') < 0) {this.className += ' hover';} };
		this.onmouseout = function() {this.className = this.className.replace(/\s*hover/, ''); };

		drag.initialise(this);
	});
	
	$("ul.draggables").each(function(i) {
		this.setAttribute('aria-labelledby', this.id + 'h');
		this.setAttribute('role', 'list');
	});
});