$(function(){
    $('a[href^="http://"]').attr({
        target: "_blank",
        title: "Opens in a new window"
    });
});