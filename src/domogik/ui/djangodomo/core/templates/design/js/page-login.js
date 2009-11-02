$(function(){
  $("#loginname").addClass("hidden");
  $("#loginname").val('');
  $("#logincode").val('');
  $("#logincode").attr('disabled', true);
  $("#digits").hide();
});

function chooseUser(id, name) {
  $("#loginname").val(name);
  $("#users li a").removeClass('selected');
  $("#"+id).addClass('selected');
  $("#logincode").attr('disabled', false);
  $("#digits").slideDown();
  $("#logincode").focus();
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
