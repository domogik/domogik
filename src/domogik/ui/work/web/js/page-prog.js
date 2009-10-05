			$(function(){
			
				// Accordion
				$("#nav2").accordion({ header: "h2" });
				$('fieldset').addClass('ui-corner-all');
				$('input.button').addClass('ui-corner-all');
				
				$('select#comp').selectmenu();
				$('select#temp').selectmenu();

					
				// Slider
				$("#slider-blind").slider({
					range: false,
					min: 0,
					max: 100,
					values: [50],
					slide: function(event, ui) {
						$("#value-blind").val(ui.values[0] + '%');
					}
				});
				$("#value-blind").val($("#slider-blind").slider("values", 0) + ' %');
			
				$(".details").hide();
				
			});
				
		function toggleScenario(id) {
			var details = $(".details");
		    if (details.is(":hidden")) {
        		details.slideDown("slow");
	      	} else {
//		  		details.slideUp("slow");
			}
		}
		

		function validForm() {
			var details = $(".details");
			details.slideUp('slow');
		}