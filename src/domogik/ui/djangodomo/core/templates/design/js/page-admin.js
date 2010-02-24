$(document).ready(function(){

	getREST('/module/list/',
		function(data) {
			var status = (data.status).toLowerCase();
			if (status == 'ok') {
				$.each(data.module, function() {
					var li = $("<li></li>");
					var a = $("<a>" + this.name + "</a>");
					a.attr('href', '');
					a.addClass("icon16-module-" + this.name);
					if (this.status == 'ON') {
						a.append("<div class='status icon16-status-active'></div>");
					} else {
						a.append("<div class='status icon16-status-inactive'></div>");					
					}
					li.append(a);
					$("#modules_list").append(li);	
				});
			} else {
				display_message('error', data.description);                                          
			}
		}
	)
});