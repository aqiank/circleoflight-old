const DELAY = 10000

var timer = 5;
var timeoutId;

$.get('/display', function(data, status) {});

$(document).ready(function() {
	$('#timer').empty();
	$('#timer').append('<p>' + timer + '</p>');
	window.setTimeout(countdown, 1000);
});

function countdown() {
	timer--;
	$('#timer').empty();
	$('#timer').append('<p>' + timer + '</p>');
	if (timer === 0) {
		$('#timer').empty();
		$('#timer').append('<p>Go!</p>');
		window.setTimeout(validate, DELAY);
		return;
	}
	window.setTimeout(countdown, 1000);
}

function validate() {
	window.location = "validate.html";
}
