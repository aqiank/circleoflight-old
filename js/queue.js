const REFRESH_TIME = 1000;

$(document).ready(function() {
	updateQueue();
});

var pos = -1;

function updateQueue() {
	var list = [];
	var queue = $('#queue');
	var timer = $('#timer');

	$.getJSON("/get_queue", function(data) {
		$.each(data, function(key, val) {
			if (key === "names") {
				list = val;
			} else if (key === "pos") {
				pos = val;
			}
		});
		queue.empty();
		for (var i = 0; i < list.length; i++) {
			if (i === pos) {
				queue.append('<div class="queue_entry_selected"><p>You (' + list[i] + ')</p></div>');
			} else {
				queue.append('<div class="queue_entry"><p>' + list[i] + '</p></div>');
			}
		}

		timer.empty();
		timer.html("" + pos);
		if (pos === 0) {
			$('#turn_form').submit();
		}
	});
	window.setTimeout(updateQueue, REFRESH_TIME);
}
