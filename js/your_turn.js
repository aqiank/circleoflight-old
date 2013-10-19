var count = 10;

$(document).ready(function() {
	countdown();
});

function countdown() {
	var counter = $('#timer');

	counter.empty();
	counter.append('<h1>' + count + '</h1>');
	
	if (count === 0) {
		$('#timeout').submit()
		return;
	}
	count--;
	window.setTimeout(countdown, 1000);
}
