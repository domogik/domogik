(function($) {
    $.create_widget({
        // default options
        options: {
            version: 0.1,
            creator: 'Domogik',
            id: 'dmg_3x2_communicationCallerId',
            name: 'Caller Id',
            description: 'Specific widget for Caller Id',
            type: 'sensor.string',
            height: 2,
            width: 3,
            filter:["communication.Caller_Id.*"],
            displayname: true,
			displayborder: true
        },

        _init: function() {
            var self = this, o = this.options;
            this.element.addClass("icon32-usage-" + o.usage)

            this._new =  $("<div class='new'></div>");
            this.element.append(this._new);
            this._list =  $("<ul></ul>");
            this.element.append(this._list);

            this._initValues(5);
        },

        _statsHandler: function(stats) {
            if (stats && stats.length > 0) {
                this.values = stats;
                this.displayList();
            } else {
                this.values = null;
            }
        },
        
        _eventHandler: function(d, value) {
            var self = this, o = this.options;
            var date = new Date();
            this._new.text(value);
            this._new.addClass("receiving");
            $.doTimeout('callerIdReceiveing', 30000, function() {
                self.values.pop();
                self.values.unshift({date:date.format("yyyy-mm-dd H:MM:ss"), value:value});
                self.displayList();
                self._new.text('');
                self._new.removeClass("receiving");
            });
        },

        displayList: function() {
            var self = this, o = this.options;
            if (this.values) {
                this._list.empty();
                $.each(this.values, function(index, stat){
                    
                    self._list.append("<li>" + stat.date + " " + stat.value + "</li>");
                });
            } else { // Unknown
            }
        }
    });
})(jQuery);

function sortDate(a, b) {
    var aDate = new Date(a.date);
    var bDate = new Date(b.date);
}