(function($) {
    $.create_widget({
        // default options
        options: {
            version: 0.1,
            creator: 'Domogik',
            id: 'dmg_1x1_minimalSensorNumber',
            name: 'Mini widget',
            description: 'Mini widget without decoration, and rounded value',
            type: 'sensor.number',
            height: 1,
            width: 1,
            displayname: false,
			displayborder: true,
			screenshot: 'images/screenshot.png'
        },

        _init: function() {
            var self = this, o = this.options;
            
            if (!o.model_parameters.unit) o.model_parameters.unit = ''; // if unit not defined, display ''
            var cell = $("<div class='cell'></div>")
            this._elementValue =  $("<div class='widget_value'></div>");
            cell.append(this._elementValue);
            this.element.append(cell);
            this._initValues(1);
        },

        _statsHandler: function(stats) {
            if (stats && stats.length > 0) {
                this.setValue(stats[0].value);
            } else {
                this.setValue(null);
            }
        },
        
        _eventHandler: function(timestamp, value) {
            this.setValue(value);
        },

        setValue: function(value) {
            var self = this, o = this.options;
            if (value) {
                var intvalue = round_number(parseFloat(value),1);
                this._elementValue.html(intvalue + ' ' + o.model_parameters.unit)
            } else { // Unknown
                this._elementValue.html('-- ' + o.model_parameters.unit)
            }
        }
    });
})(jQuery);

function round_number(number,dec_places){
//Version 2.0 (c) Copyright 2008, Russell Walker, Netshine Software Limited. www.netshinesoftware.com
var new_number='';var i=0;var sign="";number=number.toString();number=number.replace(/^\s+|\s+$/g,'');if(number.charCodeAt(0)==45){sign='-';number=number.substr(1).replace(/^\s+|\s+$/g,'')}dec_places=dec_places*1;dec_point_pos=number.lastIndexOf(".");if(dec_point_pos==0){number="0"+number;dec_point_pos=1}if(dec_point_pos==-1||dec_point_pos==number.length-1){if(dec_places>0){new_number=number+".";for(i=0;i<dec_places;i++){new_number+="0"}if(new_number==0){sign=""}return sign+new_number}else{return sign+number}}var existing_places=(number.length-1)-dec_point_pos;if(existing_places==dec_places){return sign+number}if(existing_places<dec_places){new_number=number;for(i=existing_places;i<dec_places;i++){new_number+="0"}if(new_number==0){sign=""}return sign+new_number}var end_pos=(dec_point_pos*1)+dec_places;var round_up=false;if((number.charAt(end_pos+1)*1)>4){round_up=true}var digit_array=new Array();for(i=0;i<=end_pos;i++){digit_array[i]=number.charAt(i)}for(i=digit_array.length-1;i>=0;i--){if(digit_array[i]=="."){continue}if(round_up){digit_array[i]++;if(digit_array[i]<10){break}}else{break}}for(i=0;i<=end_pos;i++){if(digit_array[i]=="."||digit_array[i]<10||i==0){new_number+=digit_array[i]}else{new_number+="0"}}if(dec_places==0){new_number=new_number.replace(".","")}if(new_number==0){sign=""}return sign+new_number}