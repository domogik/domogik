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
            this._newbg =  $("<div class='newbg'></div>");
            this.element.append(this._newbg);
            this._new =  $("<div class='new'></div>");
            this.element.append(this._new);
            this._newbg.hide();
            this._new.hide();
            this._list =  $("<ul></ul>");
            this.element.append(this._list);

            this._initValues(10);
        },

        _statsHandler: function(stats) {
            var self = this, o = this.options;
            this.values = [];
            if (stats && stats.length > 0) {
                this.previous = null;
                $.each(stats, function(index, stat){
                    self.addCall(stat);
                });
                this.displayList();
            }
        },
        
        addCall: function(stat) {
            if (stat.value != this.previous) {
                stat.number = 1;
                this.values.unshift(stat);
                this.previous = stat.value;
            } else {
                this.values[0].number++;
            }
        },
        
        _eventHandler: function(timestamp, value) {
            var self = this, o = this.options;
            this._new.text(value);
            this.addCall({timestamp:timestamp, value:value});
            this._new.show();
            this._newbg.show();
            $.doTimeout('callerIdReceiveing', 30000, function() {
                self.displayList();
                self._new.hide();
                self._newbg.hide();
            });
        },

        displayList: function() {
            var self = this, o = this.options;
            this.values.sort(sortDate);
            if (this.values) {
                this._list.empty();
                $.each(this.values, function(index, stat){
                    var date = new Date(stat.timestamp * 1000);
                    date = date.format('HH:MM');
                    if (stat.number > 1) {
                        self._list.append("<li>" + stat.value + " <span class='date'>" + date + "</span> (" + stat.number + ")</li>");                        
                    } else {
                        self._list.append("<li>" + stat.value + " <span class='date'>" + date + "</span></li>");
                    }
                });
            } else { // Unknown
            }
        }
    });
})(jQuery);

function sortDate(a, b) {
    return b.timestamp - a.timestamp;
}