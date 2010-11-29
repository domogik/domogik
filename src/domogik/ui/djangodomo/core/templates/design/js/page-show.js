$(function(){
	$(window).bind('beforeunload', function () { $.cancelRequest(); });
});

(function($) {    
    $.extend({
        initAssociations: function(page_type, page_id, device_usages, device_types) {
            var devices = [];
            var options = null;
            if (page_type == 'house') {
                options = ['base', 'feature_association', 'listdeep', 'by-house']
            } else if (page_type == 'area') {
                options = ['base', 'feature_association', 'listdeep', 'by-area', page_id];
            } else { // room
                options = ['base', 'feature_association', 'list', 'by-room', page_id];
            }
            rest.get(options,
                function(data) {
                    var status = (data.status).toLowerCase();
                    if (status == 'ok') {
                        $.each(data.feature_association, function(index, association) {
                            devices.push(association.device_feature.device_id);
                            rest.get(['base', 'ui_config', 'list', 'by-reference', 'association', association.id],
                                function(data) {
                                    var status = (data.status).toLowerCase();
                                    if (status == 'ok') {
                                        var widget = null;
                                        var place = null;
                                        $.each(data.ui_config, function(index, item) {
                                            if (item.key == 'widget') widget = item.value;
                                            if (item.key == 'place') place = item.value;
                                        });
                                        if (association.place_type == page_type || (association.place_type != page_type && place != 'otheractions')) {
                                            rest.get(['base', 'feature', 'list', 'by-id', association.device_feature_id],
                                                function(data) {
                                                    var status = (data.status).toLowerCase();
                                                    if (status == 'ok') {
                                                        var feature = data.feature[0];
                                                        var parameters_usage = $.stringToJSON(device_usages[feature.device.device_usage_id].default_options);
                                                        var parameters_type = $.stringToJSON(feature.device_feature_model.parameters);
                                                        var div = $("<div id='widget_" + association.id + "' role='listitem'></div>");
                                                        var options = {
                                                            usage: feature.device.device_usage_id,
                                                            devicename: feature.device.name,
                                                            featurename: feature.device_feature_model.name,
                                                            devicetechnology: device_types[feature.device.device_type_id].device_technology_id,
                                                            deviceaddress: feature.device.address,
                                                            featureconfirmation: feature.device_feature_model.return_confirmation,
                                                            deviceid: feature.device_id,
                                                            key: feature.device_feature_model.stat_key,
                                                            usage_parameters: parameters_usage[feature.device_feature_model.feature_type][feature.device_feature_model.value_type],
                                                            model_parameters: parameters_type
                                                        }
                                                        $("#" + association.place_type + "_" + association.place_id + " ." + place).append(div);
                                                        eval("$('#widget_" + association.id + "')." + widget + "(options)");
                                                    } else {
                                                        $.notification('error', data.description);                                          
                                                    }
                                                }
                                            );
                                        }
                                    } else {
                                        $.notification('error', data.description);                                          
                                    }
                                }
                            );
                        });
                        devices = unique(devices);
                        if (devices.length > 0) $.eventRequest(devices);
                    } else {
                        $.notification('error', data.description);                                          
                    }
                }
            );
        },

        cancelRequest: function() {
            if (this.request_ticketid)
                $.eventCancel(this.request_ticketid);
        },
        
        eventRequest: function(devices) {
            url = rest_url + '/events/request/new/' + devices.join('/') + '/';
            rest.jsonp(url,
                function (data) {
                    var status = (data.status).toLowerCase();
                    if (status == 'ok') {
                        // Free the ticket when page unload
                        this.request_ticketid = data.event[0].ticket_id;
                        $(document).trigger('dmg_event', [data.event[0]]);
                        $.eventUpdate(data.event[0].ticket_id);
                    } else {
                        $.notification('error', 'Event request  : ' + data.description);
                    }
                },
                function (xOptions, textStatus) {
                    $.notification('error', 'Event request : Lost REST server connection');
                }
            );
        },
        
        eventUpdate: function(ticket) {
            url = rest_url + '/events/request/get/' + ticket + '/';
            rest.jsonp(url,
                function (data) {
                    var status = (data.status).toLowerCase();
                    if (status == 'ok') {
                        $(document).trigger('dmg_event', [data.event[0]]);
                        $.eventUpdate(ticket);
                    } else {
                        $.notification('error', 'Event update : ' + data.description);
                    }
                },
                function (xOptions, textStatus) {
                    $.notification('error', 'Event request : Lost REST server connection');
                }
            );
        },
        
        eventCancel: function(ticket) {
            url = rest_url + '/events/request/free/' + ticket + '/';
            $.jsonp({
                cache: false,
                type: "GET",
                url: url,
                dataType: "jsonp"
            });
        },
        
        stringToJSON: function(string) {
            var str = string;
            if (str) {
                str = string.replace(/&quot;/g,'"');
            } else {
                str = '{}';
            }
            return JSON.parse(str);
        }
    });
})(jQuery);

function unique(a) {
    var r = new Array();
    o: for (var i = 0,
    n = a.length; i < n; i++) {
        for (var x = 0,
        y = r.length; x < y; x++) {
            if (r[x] == a[i]) continue o;
        }
        r[r.length] = a[i];
    }
    return r;
}
