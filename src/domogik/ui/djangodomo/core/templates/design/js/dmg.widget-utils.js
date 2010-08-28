// <![CDATA[
$(function(){
    $.fn.extend({
        moveToCircleCoord: function (options) {
            var c = getCircleCoord (options.x, options.y, options.r, options.deg);
            var x = c.x - (this.width() / 2);
            var y = c.y - (this.height() / 2);
            this.css('top', y).css('left', x);
            if (options.rotate) this.css('-moz-transform', 'rotate(' + options.deg + 'deg)').css('-webkit-transform', 'rotate(' + options.deg + 'deg)');
        },
        
        panelAddCommand: function(options) {
            var cx = this.width()/2;
            var cy = this.height()/2;
            var command = $("<div class='command'></div>");
            command.addClass(options.class)
                .click(options.click);
            this.append(command);
            command.moveToCircleCoord({x:cx, y:cy, r:options.r, deg:options.deg, rotate:options.rotate}); // ! Need to be after append
        },
        
        panelAddText: function(options) {
            var cx = this.width()/2;
            var cy = this.height()/2;
            var text = $("<div class='text'></div>");
            text.addClass(options.class);
            this.append(text);
            text.moveToCircleCoord({x:cx, y:cy, r:options.r, deg:options.deg, rotate:options.rotate}); // ! Need to be after append
        }
    });
    
    $.extend({ 
        getPanel: function(options) {
            var panel = $("<div class='widget_1x1_panel'></div>");
            panel.width(options.width)
                .height(options.height)
                .css('left', '-' + (options.width/2 - 25) + 'px')
                .css('top', '-' + (options.height/2 - 25) + 'px');
            var deco = $("<canvas class='deco' width='" + options.width + "' height='" + options.height + "'></canvas>")
            panel.append(deco);
            var canvas = deco.get(0);
            if (canvas.getContext) {
                var ctx = canvas.getContext('2d');
                ctx.beginPath();
                ctx.strokeStyle = "#BDCB2F";
                ctx.lineWidth = 2;
                ctx.arc(95,95,94,0,(Math.PI*2),true); // Outer circle  
                ctx.stroke();
                ctx.beginPath();
                ctx.strokeStyle = "#000000";
                ctx.lineWidth = 36;
                ctx.lineCap = 'round';
                ctx.arc(95,95,70,(Math.PI/180)*150,(Math.PI/180)*80,false); // Main circle  
                ctx.stroke();

                var c = getCircleCoord(95, 95, 65, 80);
                ctx.beginPath();
                ctx.strokeStyle = "#000000";
                ctx.fillStyle = "#eeeeee";
                ctx.lineWidth = 5;
                ctx.lineCap = 'butt';
                ctx.arc(c.x,c.y,20,0,(Math.PI*2),true); // Value circle  
                ctx.fill();
                ctx.stroke();
            }

            return panel;
        }
    });
});

function getCircleCoord (x, y, r, deg) {
    var res = {x:null, y:null, rad: null};
    res.rad = (Math.PI/180)*deg;
    res.x = Math.round(x + r * Math.cos(res.rad));
    res.y = Math.round(y + r * Math.sin(res.rad));
    return res;
}
// ]]>