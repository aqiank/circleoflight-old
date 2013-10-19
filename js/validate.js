$.getJSON('/preview', function(data, status) {
	var previewpath = ''
	$.each(data, function(key, val) {
		if (key === 'previewpath') {
			previewpath = val;
		}
	});

	$(document).ready(function() {
		$('#result').attr('src', previewpath);
	});
}).fail(function() {
	alert('Failed to retrieve the image result. Please try refreshing the page.');
});
