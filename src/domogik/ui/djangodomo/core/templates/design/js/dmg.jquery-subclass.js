var object = (function(){
    function F(){}
    return (function(o){
        F.prototype = o;
        return new F();
    });
})();

(function($) {
    $.widget('ui.widget');

    var OVERRIDE = /xyz/.test(function(){xyz;}) ? /\b_super\b/ : /.*/; 
    $.ui.widget.subclass = function subclass (name){
        $.widget(name); // Slightly inefficient to create a widget only to discard its prototype, but it's not too bad
        name = name.split('.');
        var widget = $[name[0]][name[1]], superclass = this, superproto = superclass.prototype;
        
        
        var args = $.makeArray(arguments); // get all the add-in methods
        var proto = args[0] = widget.prototype = object(superproto); // and inherit from the superclass
        $.extend.apply(null, args); // and add them to the prototype
        widget.subclass = subclass;
        
        // Subtle point: we want to call superclass _create, _init and _destroy if they exist
        // (otherwise the user of this function would have to keep track of all that)
        // and we want to extend the options with the superclass's options. We copy rather than subclass
        // so changing a default in the subclass won't affect the superclass
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
})(jQuery);