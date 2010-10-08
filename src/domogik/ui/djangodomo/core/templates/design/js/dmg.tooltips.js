// <![CDATA[
$(function(){
    $.fn.tooltip_left = function (){
        this.qtip({
            position: {
                corner: {
                    target: 'leftMiddle',
                    tooltip: 'rightMiddle'
                }
            },
            style: {
                padding: 5,
                background: '#A2D959',
                color: 'black',
                textAlign: 'center',
                border: {
                    width: 7,
                    radius: 5,
                    color: '#A2D959'
                },
                tip: 'rightMiddle',
                name: 'dark' // Inherit the rest of the attributes from the preset dark style
            }
        });
        return this;
    };
    
    $.fn.tooltip_right = function (){
        this.qtip({
            position: {
                corner: {
                    target: 'rightMiddle',
                    tooltip: 'leftMiddle'
                }
            },
            style: {
                padding: 5,
                background: '#A2D959',
                color: 'black',
                textAlign: 'center',
                border: {
                    width: 7,
                    radius: 5,
                    color: '#A2D959'
                },
                tip: 'leftMiddle',
                name: 'dark' // Inherit the rest of the attributes from the preset dark style
            }
        });
        return this;
    };
    
    $.fn.tooltip_top = function (){
        this.qtip({
            position: {
                corner: {
                    target: 'topMiddle',
                    tooltip: 'bottomMiddle'
                }
            },
            style: {
                padding: 5,
                background: '#A2D959',
                color: 'black',
                textAlign: 'center',
                border: {
                    width: 7,
                    radius: 5,
                    color: '#A2D959'
                },
                tip: 'bottomMiddle',
                name: 'dark' // Inherit the rest of the attributes from the preset dark style
            }
        });
        return this;
    };

    $.fn.tooltip_bottom = function (){
        this.qtip({
            position: {
                corner: {
                    target: 'bottomMiddle',
                    tooltip: 'topMiddle'
                }
            },
            style: {
                padding: 5,
                background: '#A2D959',
                color: 'black',
                textAlign: 'center',
                border: {
                    width: 7,
                    radius: 5,
                    color: '#A2D959'
                },
                tip: 'topMiddle',
                name: 'dark' // Inherit the rest of the attributes from the preset dark style
            }
        });
        return this;
    };
    
    $.fn.tooltip_content_right = function (opts){
        this.qtip({
            position: {
                corner: {
                    target: 'rightBottom',
                    tooltip: 'leftTop'
                }
            },
            style: {
                padding: 5,
                background: '#A2D959',
                color: 'black',
                textAlign: 'left',
                border: {
                    width: 7,
                    radius: 5,
                    color: '#A2D959'
                },
                tip: 'leftTop',
                name: 'dark' // Inherit the rest of the attributes from the preset dark style
            },
            content: opts.content
        });
        return this;
    };
});
// ]]>