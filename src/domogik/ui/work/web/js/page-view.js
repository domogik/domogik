			$(function(){
			
				// Accordion
				$("#nav2").accordion({ header: ".section" });
				
				//Room Page
				$('select#heat-mode').selectmenu();
				
				// Slider heat temperature
				$("#slider-heat-temp").slider({
					range: true,
					min: 10,
					max: 25,
					values: [18, 20],
					slide: function(event, ui) {
						$("#value-heat-tempmin").val(ui.values[0] + ' \u00B0C');
						$("#value-heat-tempmax").val(ui.values[1] + ' \u00B0C');
					}
				});
				$("#value-heat-tempmin").val($("#slider-heat-temp").slider("values", 0) + ' \u00B0C');
				$("#value-heat-tempmax").val($("#slider-heat-temp").slider("values", 1) + ' \u00B0C');

			// Slider light
				$("#slider-light-2").slider({
					range: false,
					min: 0,
					max: 100,
					value: 50,
					slide: function(event, ui) {
						$("#value-light-2").val(ui.value + ' %');
					}
				});
				$("#value-light-2").val($("#slider-light-2").slider("value") + ' %');
});
				
