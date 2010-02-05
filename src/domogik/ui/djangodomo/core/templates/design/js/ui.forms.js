function updateTips(tips, t) {
	tips.text(t).effect("highlight", {},
	1500);
}

function checkLength(tips, o, n, min, max) {
	if (o.val().length > max || o.val().length < min) {
		o.addClass('ui-state-error');
		updateTips(tips, "La longueur de " + n + " doit tre comprise entre " + min + " et " + max + ".");
		return false;
	} else {
		return true;
	}

}

function updateTips(t) {
	tips.text(t).effect("highlight", {},
	1500);
}

function checkLength(o, n, min, max) {

	if (o.val().length > max || o.val().length < min) {
		o.addClass('ui-state-error');
		updateTips("La longueur de " + n + " doit tre comprise entre " + min + " et " + max + ".");
		return false;
	} else {
		return true;
	}

}