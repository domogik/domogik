$(function(){
  $("#loginname").addClass("hidden");
  $("#loginname").val('');
  $("#logincode").val('');
});

function chooseUser(id, name) {
  $("#loginname").val(name);
  $("#users li a").removeClass('selected');
  $("#"+id).addClass('selected');
}

function addDigit(digit) {
  var initial = $("#logincode").val();
  $("#logincode").val(initial+digit);
}

function resetDigit() {
  $("#logincode").val('');
}

function removeLastDigit() {
  var initial = $("#logincode").val();
  var final = initial.substr(0, initial.length-1);
  $("#logincode").val(final);
}
