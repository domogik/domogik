$(function(){
	$(window).bind('beforeunload', function () { $.cancelRequest(); });
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
    },
    
    getREST: function(parameters, callback) {
        url = rest_url + '/';
        // Build the REST url
        $.each(parameters, function(){
            url += encodeURIComponent(this) + '/';     
        });
        $.ajax({
            cache: false,
            type: "GET",
            url: url,
            dataType: "jsonp",
            success:
                callback,
            error:
                function(XMLHttpRequest, textStatus, errorThrown) {
                    $.notification('error', 'Event request  :' + XMLHttpRequest.readyState + ' ' + XMLHttpRequest.status + ' ' + textStatus + ' ' + errorThrown);
                }
        });
    },

    cancelRequest: function() {
        if (this.request_ticketid)
            $.eventCancel(this.request_ticketid);
        if (this.request_xOptions)
            this.request_xOptions.abort();
    },
    
    eventRequest: function(devices) {
        url = rest_url + '/events/request/new/' + devices.join('/') + '/';
        this.request_xOptions = $.jsonp({
            cache: false,
            callbackParameter: "callback",
            type: "GET",
            url: url,
            dataType: "jsonp",
            error: function (xOptions, textStatus) {
                $.notification('error', 'Event request : Lost REST server connection');
            },
            success: function (data) {
                var status = (data.status).toLowerCase();
                if (status == 'ok') {
                    // Free the ticket when page unload
                    this.request_ticketid = data.event[0].ticket_id;
                    $(document).trigger('dmg_event', [data.event[0]]);
                    $.eventUpdate(data.event[0].ticket_id);
                } else {
                    $.notification('error', 'Event request  : ' + data.description);
                }
            }
        });
    },
    
    eventUpdate: function(ticket) {
        url = rest_url + '/events/request/get/' + ticket + '/';
        this.request_xOptions = $.jsonp({
            cache: false,
            callbackParameter: "callback",
            type: "GET",
            url: url,
            dataType: "jsonp",
            error: function (xOptions, textStatus) {
                $.notification('error', 'Event update : Lost REST server connection');
            },
            success: function (data) {
                var status = (data.status).toLowerCase();
                if (status == 'ok') {
                    $(document).trigger('dmg_event', [data.event[0]]);
                    $.eventUpdate(ticket);
                } else {
                    $.notification('error', 'Event update : ' + data.description);
                }
            }
        });
    },
    
    eventCancel: function(ticket) {
        url = rest_url + '/events/request/free/' + ticket + '/';
        $.jsonp({
            cache: false,
            type: "GET",
            url: url,
            dataType: "jsonp"
        });
    }
});