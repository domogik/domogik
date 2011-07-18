$(function(){    
    $('#dialog').dialog({ width:'auto',
        position: ['middle', 100],
        resizable: true,
        modal: false
    });

    $("li#showmenu a").click(function(){
        $("#panel").toggle();      
    });
    $("li#showmodels a").click(function(){
        $('#dialog').dialog('open');
    });
    
    $('.features, #widgets ul, #model dl').hide();
    
    $('button.device').click(function() {
        $('button.device, button.feature').removeClass('selected');
        $(this).addClass('selected');
        $('.features, #widgets ul, #model dl').hide();
        var deviceid = $(this).attr('deviceid');
        $('#features' + deviceid).show().focus();
    });
    
    $("button.feature").click(function(){
        $('button.feature').removeClass('selected');
        $(this).addClass('selected');
        var featuretype = $(this).attr('featuretype');
        var featureid = $(this).attr('featureid');
        var featuremodel = $(this).attr('featuremodel');
        var featurename = $(this).attr('featurename');
        var devicename = $(this).attr('devicename');
        $("#model dl").hide();
        $("#widgets ul").widget_models({
            featuretype: featuretype,
            featureid: featureid,
            featuremodel: featuremodel,
            featurename: featurename,
            devicename: devicename
        });
        $("#widgets ul").show();
    });

});

(function($) {
    
    function ondrop(event, ui) {
        var helper = ui.draggable.draggable( "option", "helper" );
        var item = null;
        if (helper == 'clone') {
            item = $(ui.helper).clone();
            item.removeAttr('style');
            $(this).append(item);
            item.widget_shape({
                widgetid: ui.draggable.data('widgetid'),
                featureid: ui.draggable.data('featureid'),
                featurename: ui.draggable.data('featurename'),
                devicename: ui.draggable.data('devicename'),
                associationid: ui.draggable.data('associationid'),
                widgetwidth: ui.draggable.data('widgetwidth'),
                widgetheight: ui.draggable.data('widgetheight'),

                draggable:{
                    helper: false,
                    revert: 'invalid',
                    drag: ondrag,
                    stop: onstop
                },
                deletable: true
            });            
        } else {
            item = ui.draggable.detach();
            item.removeAttr('style');
            $(this).append(item);
        }
        $.addAssociation(item, $(this));            
        return false;
    }
    
    function onstop(event, ui) {
        $(".ui-dialog").show();
    }
    
    function ondrag(event, ui) {
        $(".ui-dialog").hide();
    }
    
    $.fn.extend({
	    displayName: function(){
            _devicename = $("<div class='identity identitydevice length" + this.data('widgetwidth') + "'>" + this.data('devicename') + "</div>");
            this.append(_devicename);
            _featurename = $("<div class='identity identityfeature length" + this.data('widgetheight') + "'>" + this.data('featurename') + "</div>");
            this.append(_featurename);
        },
        hasSize: function(width, height) {
            var id = this.data('widgetid');
            if (id) {
                var woptions = get_widgets_options(id)
                return (width == woptions.width && height == woptions.height);                
            } else {
                return false;
            }
        },
        deletable: function() {
            var self = this;
            this.addClass('deletable')
                .append('<button><span class=\'offscreen\'>Effacer</span></button>')
                .find('button').click(function(){
                        var association = self.data('associationid');
                        if (association) {
                            rest.get(['base', 'feature_association', 'del', 'id', association],
                                function(data) {
                                    var status = (data.status).toLowerCase();
                                    if (status == 'ok') {
                                        rest.get(['base', 'ui_config', 'del', 'by-reference', 'association', association],
                                            function(data) {
                                                var status = (data.status).toLowerCase();
                                                if (status == 'ok') {
                                                    self.remove();                    
                                                } else {
                                                    $.notification('error', data.description);                                          
                                                }
                                            }
                                        );
                                    } else {
                                        $.notification('error', data.description);                                          
                                    }
                                }
                            );
                        }
                });
        }
	});
    
    /* Mini Widget */
    $.ui.widget.subclass("ui.widget_models", {
        // default options
        options: {
        },

        _init: function() {
            var self = this, o = this.options;
            this.element.empty();
            var widgets = get_widgets(o.featuretype);
            $.each(widgets, function(index, id) {
                var woptions = get_widgets_options(id);
                if (matchFilter(woptions.filters, o.featuremodel)) {
                    var widget = $("<li><button class='widget'>" + woptions.name + "</button></li>");
                    widget.find('button').click(function() {
                        $('.widget').removeClass('selected');
                        $(this).addClass('selected');
                        $('#model').widget_model({
                            widgetid: id,
                            widgetwidth: o.width,
                            widgetheight: o.height,
                            featureid: o.featureid,
                            featurename: o.featurename,
                            devicename: o.devicename
                        });
                        $("#model dl").show();
                    });
                    self.element.append(widget); 
                }
            });
        },
	
        update: function() {
            this._init();
        }
    });
    
    $.ui.widget.subclass("ui.widget_model", {
        // default options
        options: {
        },

        _init: function() {
            var self = this, o = this.options;
            var woptions = get_widgets_options(o.widgetid)
            if (woptions) {
                o = $.extend ({}, woptions, o);
            }
            this.element.find('dt.model').text(woptions.name);
            this.element.find('dd.version').text(woptions.version);
            this.element.find('dd.author').text(woptions.creator);
            this.element.find('dd.description').text(woptions.description);
            if (woptions.screenshot) {
                this.element.find('dd.screenshot').html("<img src='/widgets/" + woptions.id + "/" + woptions.screenshot + "' />");
            } else {
                this.element.find('dd.screenshot').empty();                
            }
            var model = $('<div></div>');
            model.widget_shape({
                widgetid: o.widgetid,
                widgetwidth: o.width,
                widgetheight: o.height,
                featureid: o.featureid,
                featurename: o.featurename,
                devicename: o.devicename,
                draggable: {
                    helper: "clone",
                    revert: 'invalid',
                    appendTo: 'body',
                    drag: ondrag,
                    stop: onstop
                }
            });
            this.element.find('dd.model')
                .empty()
                .append(model);
        }
    });
    
    $.ui.widget.subclass("ui.widget_shape", {
        // default options
        options: {
            deletable: false
        },

        _init: function() {
            var self = this, o = this.options;
            var woptions = get_widgets_options(o.widgetid)
            if (woptions) {
                o = $.extend ({}, woptions, o);
            }
            this.element.addClass('shape');
            this.element.removeAttr('style');
            this.element.attr('role', 'listitem');
			this.element.addClass('size' + o.width + 'x' + o.height);
            this.element.attr("tabindex", 0);
            this.element.append("<div class='sizetext'>" + o.width + 'x' + o.height + "</div>");
            this.element.data({
                'devicename':o.devicename,
                'featurename':o.featurename,
                'featureid':o.featureid,
                'widgetwidth': o.width,
                'widgetheight':o.height,
                'widgetid': o.widgetid,
                'associationid': o.associationid
            });
            this.element.displayName();
            this.element.draggable(o.draggable);
            if (o.deletable) this.element.deletable();            
        }
    });
 
    $.extend({
        addAssociation: function(model, zone) {
            var page_type = zone.data('page_type');
            var page_id = zone.data('page_id');
            var place_id = zone.data('place');
            var widget_id = model.data('widgetid');
            var feature_id = model.data('featureid');
            rest.get(['base', 'feature_association', 'add', 'feature_id', feature_id, 'association_type', page_type, 'association_id', page_id],
                function(data) {
                    var status = (data.status).toLowerCase();
                    if (status == 'ok') {
                        var id = data.feature_association[0].id;
                        rest.get(['base', 'ui_config', 'set', 'name', 'association', 'reference', id, 'key', 'widget', 'value', widget_id],
                            function(data) {
                                var status = (data.status).toLowerCase();
                                if (status == 'ok') {
                                    rest.get(['base', 'ui_config', 'set', 'name', 'association', 'reference', id, 'key', 'place', 'value', place_id],
                                        function(data) {
                                            var status = (data.status).toLowerCase();
                                            if (status == 'ok') {
                                                model.data('associationid', id);
                                            } else {
                                                $.notification('error', data.description);                                          
                                            }
                                        }
                                    );
                                } else {
                                    $.notification('error', data.description);                                          
                                }
                            }
                        );
                    } else {
                        $.notification('error', data.description);                                          
                    }
                }
            );
        },
        
        initAssociations: function(page_type, page_id) {
            $('.maininfo').droppable({
                    activeClass: 'state-active',
                    hoverClass: 'state-hover',
                    accept: function(draggable) {
                        return (($(".model", this).length  < 1) && draggable.hasSize(1, 1));
                    },
                    drop: ondrop
            })
                .data({'place':'maininfo','page_type': page_type,'page_id':page_id});

            
            $('.mainactions').droppable({
                    activeClass: 'state-active',
                    hoverClass: 'state-hover',
                    accept: function(draggable) {
                        return (($(".model", this).length  < 4) && draggable.hasSize(1, 1));
                    },
                    drop: ondrop
            })
                .data({'place':'mainactions','page_type': page_type,'page_id':page_id});
            
            $('.otheractions').droppable({
                    activeClass: 'state-active',
                    hoverClass: 'state-hover',
                    accept: function(draggable) {
                        return (draggable.hasClass('shape'));
                    },
                    drop: ondrop
            })
                .data({'place':'otheractions','page_type': page_type,'page_id':page_id});
    
            var options = null;
            if (page_type == 'house') {
                options = ['base', 'feature_association', 'list', 'by-house']
            } else {
                options = ['base', 'feature_association', 'list', 'by-' + page_type, page_id];
            }
            rest.get(options,
                function(data) {
                    var status = (data.status).toLowerCase();
                    if (status == 'ok') {
                        $.each(data.feature_association, function(index, association) {
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
                                        rest.get(['base', 'feature', 'list', 'by-id', association.device_feature_id],
                                            function(data) {
                                                var status = (data.status).toLowerCase();
                                                if (status == 'ok') {
                                                    var model = $("<div id='" + association.id + "' role='listitem'></div>");
                                                    model.widget_shape({
                                                        widgetid: widget,
                                                        featureid: association.device_feature_id,
//                                                            featuremodel: data.feature[0].device_feature_model.id,
                                                        featurename: data.feature[0].device_feature_model.name,
                                                        devicename: data.feature[0].device.name,
                                                        associationid: association.id,
                                                        draggable: {
                                                            helper: false,
                                                            revert: 'invalid',
                                                            drag: ondrag,
                                                            stop: onstop
                                                        },
                                                        deletable: true
                                                    });
                                                    $("." + place).append(model);
                                                } else {
                                                    $.notification('error', data.description);                                          
                                                }
                                            }
                                        );
                                    } else {
                                        $.notification('error', data.description);                                          
                                    }
                                }
                            );
                        });
                    } else {
                        $.notification('error', data.description);                                          
                    }
                }
            );
        }
    });
    
    function matchFilter(filters, id) {
        var res = false;
        if (filters) {
            $.each(filters, function(index, filter){
                var afilter = filter.split('.');
                var aid = id.split('.');
                res =  (afilter[0] == aid[0] || afilter[0] == '*') && (afilter[1] == aid[1] || afilter[1] == '*') && (afilter[2] == aid[2] || afilter[2] == '*');
            });
        } else {
            res = true;
        }
        return res;
    }
})(jQuery);