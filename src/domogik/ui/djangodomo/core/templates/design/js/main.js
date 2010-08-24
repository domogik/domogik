$(function(){
   	$("body").attr('role', 'application');
	$(window).bind('beforeunload', function () { $.cancelRequest(); });
});
