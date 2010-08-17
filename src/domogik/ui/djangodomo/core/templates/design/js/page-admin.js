function getPluginsList() {
	$("#plugins_list li").remove();
	$.getREST(['plugin', 'list'],
		function(data) {
			var status = (data.status).toLowerCase();
			if (status == 'ok') {
                if (data.plugin.length > 0) { // If a least 1 plugin is enabled
                    $.each(data.plugin, function() {
                        var technology = this.technology.replace(' ', '');
                        if ($("#plugins_list ul#menu_" + technology).length == 0) {
                            $("#plugins_list").append("<li><div class='titlenav2 icon16-technology-" + technology + "'>" + technology + "</div><ul id='menu_" + technology + "'></ul></li>")
                        }
                        var li = $("<li></li>");
                        var a = $("<a></a>");
                        a.attr('href', '/domogik/admin/plugin/' + this.name)
                            .attr('title', this.description)
                            .tooltip_right();
                        var status = $("<div>" + this.name + "</div>");
                        if (this.name != 'rest') {
                            status.addClass("menu-indicator")
                            if (this.status == 'ON') {
                                status.addClass("icon16-status-active");
                                status.append("<span class='offscreen'>Running</span>");
                            } else {
                                status.addClass("icon16-status-inactive");
                                status.append("<span class='offscreen'>Stopped</span>");
                            }
                        }
                        a.append(status);
                        li.append(a);
                        $("#plugins_list ul#menu_" + technology).append(li);	
                    });
                } else {
                    var li = $("<li></li>");
                    var a = $("<a>No plugin enabled yet<br />Click to reload</a>");
                    a.attr('href', '#');
                    a.addClass("icon16-status-error");
                    a.click(function(){getPluginsList();})
                    li.append(a);
                    $("#plugins_list").append(li);
                }
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