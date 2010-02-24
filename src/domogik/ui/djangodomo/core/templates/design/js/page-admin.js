function getModulesList() {
	$("#modules_list li").remove();
	getREST('/module/list/',
		function(data) {
			var status = (data.status).toLowerCase();
			if (status == 'ok') {
				$.each(data.module, function() {
					var li = $("<li></li>");
					var a = $("<a>" + this.name + "</a>");
					a.attr('href', server_url + '/admin/modules/' + this.name);
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
				var li = $("<li></li>");
				var a = $("<a>" + data.description + " <br />Click to reload</a>");
				a.attr('href', '#');
				a.addClass("icon16-status-error");
				a.click(function(){getModulesList();})
				li.append(a);
				$("#modules_list").append(li);	
			}
		}
	)	
}

$(document).ready(function(){
	getModulesList();
});