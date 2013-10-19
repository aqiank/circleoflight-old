var previewUrl = '';
var imageUrl = '';
var showEmailForm = false;

$.getJSON("/share", function(data) {
	$.each(data, function(key, val) {
		if (key === "previewUrl") {
			previewUrl = val;
		} else if (key === "imageUrl") {
			imageUrl = val;
		}
	});
	
	$(document).ready(function() {
		$('#result').attr('src', previewUrl);
		
		$('#imgur_url').attr('href', imageUrl);

		$('#facebook').attr('href', 'https://www.facebook.com/sharer/sharer.php?u=' + imageUrl);

		$('#twitter').attr('href', 'https://twitter.com/share?url=' + imageUrl);

		$('#email_form_toggle').click(function() {
			showEmailForm = !showEmailForm;
			if (showEmailForm === true) {
				$('#email_form').css('display', 'block');
			} else {
				$('#email_form').css('display', 'none');
			}
		});
	});
}).fail(function() {
	alert('Failed to request links for the image. Please try refreshing the page.');
});
