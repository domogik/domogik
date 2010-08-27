// <![CDATA[
$(function(){
    $.fn.extend({
        moveToCircleCoord: function (options) {
            var c = getCircleCoord (options.x, options.y, options.r, options.deg);
            var x = c.x - (this.width() / 2);
            var y = c.y - (this.height() / 2);
            this.css('top', y).css('left', x);
            if (options.rotate) this.css('-moz-transform', 'rotate(' + options.deg + 'deg)').css('-webkit-transform', 'rotate(' + options.deg + 'deg)');
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