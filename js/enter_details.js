var imgfiles = [];
var prev = null;
var current = null;

$.getJSON('/get_samples', function(data) {
	$.each(data, function(key, val) {
		if (key === 'files') {
			imgfiles = val;
		}
	});

	$(document).ready(function() {
		var samples = $('.samples');
		for (var i = 0; i < imgfiles.length; i++) {
			samples.append('<span class="sample"><img src="' + imgfiles[i] + '"></span>');
		}
			$(document).on('click', '.sample img', function(e) {
			prev = current;
			if (prev != null) {
				prev.removeClass('selected');
			}
			current = $(this);
			current.addClass('selected');
			e.preventDefault();
		});

		$('.samples').css('width', '' + (100 * imgfiles.length + 2) + 'px');

		$('#submit_sample').click(function() {
			if (current === null)
				return;
			$.post('/submit_sample', current.attr('src') + '\n', function() {
				window.location = '/photo_taking.html';
			}).fail(function() {
				alert('Oops! Submission request failed. Please try again.');
			});
		});
	});
}).fail(function() {
	alert('Failed to load some images. Please refresh the page');
});
