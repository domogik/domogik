var rinor = new RINOR();

$(function(){
	$(window).bind('beforeunload', function () { rinor.cancelAll(); });
});

$.extend({
    URLEncode: function(c) {
        var o = '';
        var x = 0;
        c = c.toString();
        var r = /(^[a-zA-Z0-9_.]*)/;
        while (x < c.length) {
            var m = r.exec(c.substr(x));
            if (m != null && m.length > 1 && m[1] != '') {
                o += m[1];
                x += m[1].length;
            } else {
                if (c[x] == ' ') o += '+';
                else {
                    var d = c.charCodeAt(x);
                    var h = d.toString(16);
                    o += '%' + (h.length < 2 ? '0': '') + h.toUpperCase();
                }
                x++;
            }
        }
        return o;
    },
    
    URLDecode: function(s) {
        var o = s;
        var binVal, t;
        var r = /(%[^%]{2})/;
        while ((m = r.exec(o)) != null && m.length > 1 && m[1] != '') {
            b = parseInt(m[1].substr(1), 16);
            t = String.fromCharCode(b);
            o = o.replace(m[1], t);
        }
        return o;
    },

    getUrlVars: function(){
        var vars = [], hash;
        var hashes = window.location.href.slice(window.location.href.indexOf('?') + 1).split('&');
        for(var i = 0; i < hashes.length; i++)
        {
            hash = hashes[i].split('=');
            vars.push(hash[0]);
            vars[hash[0]] = $.URLDecode(hash[1]);
        }
        return vars;
    },
  
    getUrlVar: function(name){
        return $.getUrlVars()[name];
    },

    reloadPage: function(data) {
        var newlocation = window.location.href.substring(0, window.location.href.indexOf('?'));
        newlocation += "?";
        $.each(data, function(key, value) {
            newlocation += key + "=" + value + "&";
        });
        window.location = newlocation;
    },

    loadPage: function(url, data) {
        var newlocation = url;
        newlocation += "?";
        $.each(data, function(key, value) {
            newlocation += key + "=" + value + "&";
        });
        window.location = newlocation;
    }
});

function RINOR() {
    this.uid = 0;
    this.processing = new Array();
}

RINOR.prototype.get = function(parameters, callback) {
    var self = this;
    url = rinor_url + '/';
    // Build the RINOR url
    $.each(parameters, function(){
        url += encodeURIComponent(this) + '/';     
    });
    return this.jsonp(url, callback,
                      function(xOptions, textStatus) {$.notification('error', 'RINOR communication : ' + textStatus + ' (' + url + ')');}
            );
}

RINOR.prototype.jsonp = function(url, successCallback, errorCallback) {
    var self = this;
    return $.jsonp({
        cache: false,
        type: "GET",
        url: url,
        dataType: "jsonp",
        callback: "_" + self.getuid(),
        callbackParameter: "callback",
        beforeSend: function(xOptions) {
            self.register(xOptions);
        },
        complete: function(xOptions) {
            self.unregister(xOptions);
        },
        success:
            successCallback,
        error:
            errorCallback
    });
}

RINOR.prototype.register = function(xOptions) {
    this.processing[xOptions.callback] = xOptions;
    return xOptions.callback;
}

RINOR.prototype.unregister = function(xOptions) {
    delete this.processing[xOptions.callback];
}

RINOR.prototype.getuid = function() {
    return this.uid++;
}

RINOR.prototype.cancel = function(id) {
    if (id) {
        xOptions = this.processing[id];
        if (xOptions) {
            xOptions.abort();
            this.unregister(id);
        }        
    }
}

RINOR.prototype.cancelAll = function(id) {
    for (var i in this.processing) {
        this.processing[i].abort();
    }
}
