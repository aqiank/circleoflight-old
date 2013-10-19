const MAX_USER_TIME = 180;

var user_time = 0;

checkUserTime();

function checkUserTime() {
	$.getJSON("/get_user_time", function(data) {
		$.each(data, function(key, val) {
			if (key === 'user_time') {
				user_time = int(val);
			}
		});
		if (user_time > 0) {
			alert('You have ' + user_time + ' seconds left.');
		} else if (user_time <= 0) {
			alert('Your user session has expired. Returning to home page.');
		}
	}).fail(function() {'Failed to get user time. Please try refeshing the page.'});
	window.setTimeout(checkUserTime, 1000);
}
