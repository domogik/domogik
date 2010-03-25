function getPluginsList() {
	$("#plugins_list li").remove();
	getREST('/plugin/list/',
		function(data) {
			var status = (data.status).toLowerCase();
			if (status == 'ok') {
				$.each(data.plugin, function() {
					var li = $("<li></li>");
					var a = $("<a></a>");
					a.attr('href', server_url + '/admin/plugin/' + this.name)
						.attr('title', this.description)
						.addClass("icon16-technology-" + this.technology)
						.tooltip_right();
					var status = $("<div>" + this.name + "</div>");
					status.addClass("menu-indicator")
					if (this.status == 'ON') {
						status.addClass("icon16-status-active");
						status.append("<span class='offscreen'>Running</span>");
					} else {
						status.addClass("icon16-status-inactive");
						status.append("<span class='offscreen'>Stopped</span>");
					}
					li.append(a);
					a.append(status);
					$("#plugins_list").append(li);	
				});
			} else {
				var li = $("<li></li>");
				var a = $("<a>" + data.description + " <br />Click to reload</a>");
				a.attr('href', '#');
				a.addClass("icon16-status-error");
				a.click(function(){getPluginsList();})
				li.append(a);
				$("#plugins_list").append(li);	
			}
		}
	)	
}

$(document).ready(function(){
	getPluginsList();
	$('#plugins_list li a[title]').tooltip_right();
});