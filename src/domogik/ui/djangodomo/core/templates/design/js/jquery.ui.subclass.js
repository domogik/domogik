// http://bililite.com/blog/extending-jquery-ui-widgets/
// Copyright (c) 2009 Daniel Wachsstock
// MIT license:
// Permission is hereby granted, free of charge, to any person
// obtaining a copy of this software and associated documentation
// files (the "Software"), to deal in the Software without
// restriction, including without limitation the rights to use,
// copy, modify, merge, publish, distribute, sublicense, and/or sell
// copies of the Software, and to permit persons to whom the
// Software is furnished to do so, subject to the following
// conditions:

// The above copyright notice and this permission notice shall be
// included in all copies or substantial portions of the Software.

// THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
// EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
// OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
// NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
// HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
// WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
// FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
// OTHER DEALINGS IN THE SOFTWARE.
(function($){
// create the master widget
$.widget("ui.widget",{
	// Aspect Oriented Programming tools from Justin Palmer's article
	yield: null,
	returnValues: { },
	before: function(method, f) {
		var original = this[method];
		this[method] = function() {
			f.apply(this, arguments);
			return original.apply(this, arguments);
		};
	},
	after: function(method, f) {
		var original = this[method];
		this[method] = function() {
			this.returnValues[method] = original.apply(this, arguments);
			return f.apply(this, arguments);
		}
	},
	around: function(method, f) {
		var original = this[method];
		this[method] = function() {
			var tmp = this.yield;
			this.yield = original;
			var ret = f.apply(this, arguments);
			this.yield = tmp;
			return ret;
		}
	}
});

// from http://groups.google.com/group/comp.lang.javascript/msg/e04726a66face2a2 and
// http://webreflection.blogspot.com/2008/10/big-douglas-begetobject-revisited.html
var object = (function(F){
	return (function(o){
			F.prototype = o;
			return new F();
	});
})(function (){});

// create a widget subclass
var OVERRIDE = /xyz/.test(function(){xyz;}) ? /\b_super\b/ : /.*/; 
$.ui.widget.subclass = function subclass(name){
	$.widget(name); // Slightly inefficient to create a widget only to discard its prototype, but it's not too bad
	name = name.split('.');
	var widget = $[name[0]][name[1]], superclass = this, superproto = superclass.prototype;
	
	
	var proto = arguments[0] = widget.prototype = object(superproto); // inherit from the superclass
	$.extend.apply(null, arguments); // and add other add-in methods to the prototype
	widget.subclass = subclass;

	// Subtle point: we want to call superclass init and destroy if they exist
	// (otherwise the user of this function would have to keep track of all that)
	for (key in proto) if (proto.hasOwnProperty(key)) switch (key){
		case '_create':
			var create = proto._create;
			proto._create = function(){
				superproto._create.apply(this);
				create.apply(this);
			};
		break;
		case '_init':
			var init = proto._init;
			proto._init = function(){
				superproto._init.apply(this);
				init.apply(this);
			};
		break;
		case 'destroy':
			var destroy = proto.destroy;
			proto.destroy = function(){
				destroy.apply(this);
				superproto.destroy.apply(this);
			};
		break;
		case 'options':
			var options = proto.options;
			proto.options = $.extend ({}, superproto.options, options);
		break;
		default:
			if ($.isFunction(proto[key]) && $.isFunction(superproto[key]) && OVERRIDE.test(proto[key])){
				proto[key] = (function(name, fn){
					return function() {
						var tmp = this._super;
						this._super = superproto[name];
						try { var ret = fn.apply(this, arguments); }   
						finally { this._super = tmp; }					
						return ret;
					};
				})(key, proto[key]);
			}
		break;
	}
};
})(jQuery)