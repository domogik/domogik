(function($) {
    $.create_widget({
        // default options
        options: {
            version: 0.1,
            creator: 'Domogik',
            id: 'dmg_6x5_webcamMJPEG',
            name: 'Image Stream',
            description: 'Widget for displaying Webcam MJPEG stream',
            type: 'sensor.string',
            height: 5,
            width: 6,
            filters:['camera.webcam.mjpeg'],
            displayname: false,
			displayborder: false
        },

        _init: function() {
            var self = this, o = this.options;
            this.image = $('<img />');
            this.image.attr('src', o.deviceaddress);
            this.element.append(this.image);
        },

        _statsHandler: function(stats) {
        },
        
        _eventHandler: function(timestamp, value) {
        },

        setValue: function(value, unit, previous) {
        }
    });
})(jQuery);
