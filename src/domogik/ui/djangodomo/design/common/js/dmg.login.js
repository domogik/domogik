$(function() {
    initLogin();
    $('a.admin_required').click(function(event){openlogin($(this).attr('href'));event.preventDefault();})
});

function openlogin(path) {
    rest.get(['account', 'user', 'list'],
		function(data) {
			var status = (data.status).toLowerCase();
			if (status == 'ok') {
                var dialog = $("<div id='login' title='Identification'></div>");
                $('body').append(dialog);
                dialog.dialog({ width:'40em', resizable: false,
                                modal: true,
                                position: ['middle',50],
                                close: function(ev, ui) {
                                    $(this).remove();
                                }
                            });

                var form = $("<form id='loginForm' method='POST' action='/admin/login/?next=" + path + "'></form>");
                form.append("<div class='columnleft'><h2>1. Select a user</h2><div id='resetLogin' class='buttontext'>Change User</div><input id='loginname' name='login' type='text' /><ul id='users'></ul></div>");
                $.each(data.account, function() {
                    var account = this;
                    $('#users', form).append("<li><a href='#' id='id" + account.login + "'><img src='/design/common/images/userid.jpg' alt='' width='64' height='64' />" + account.person.first_name + "</a></li>");
                    $('#id' + account.login, form).click(function(){chooseUser('id' + account.login, account.login);});
                });
                
                form.append("<div class='columnright'><h2>2. Enter your code</h2><div id='code'><input id='logincode' name='password' type='password' value='' /><div id='submit' class='buttonok'>Ok</div></div><ul id='digits'><li><a href='#' onclick='addDigit(0);'>0</a></li><li><a href='#' onclick='addDigit(1);'>1</a></li><li><a href='#' onclick='addDigit(2);'>2</a></li><li><a href='#' onclick='addDigit(3);'>3</a></li><li><a href='#' onclick='addDigit(4);'>4</a></li><li><a href='#' onclick='addDigit(5);'>5</a></li><li><a href='#' onclick='addDigit(6);'>6</a></li><li><a href='#' onclick='addDigit(7);'>7</a></li><li><a href='#' onclick='addDigit(8);'>8</a></li><li><a href='#' onclick='addDigit(9);'>9</a></li><li><a href='#' onclick='removeLastDigit();'>C</a></li><li><a href='#' onclick='resetDigit();'>Del.</a></li></ul></div>");
                dialog.append(form);
                initLogin();
            } else {
                $.notification('error', 'Impossible to list Accounts (' + data.description + ')');
			}
		}
	)
}

function closelogin() {
    $("#login").remove();
    $("#body-overlay").remove();
}

function initLogin() {
    $("#loginForm .columnright").hide();
    $("#resetLogin").click(function(e){resetLogin(); e.stopPropagation();});
    $("#submit").click(function(e){$("#loginForm").submit(); e.stopPropagation();})
        .keypress(function (e) {if (e.which == 13 || e.which == 32) {$("#loginForm").submit(); e.stopPropagation();}});    
    $("#logincode").keypress(function (e) {if (e.which == 13 || e.which == 32) {$("#loginForm").submit(); e.stopPropagation();}});
    $("#loginname").addClass("hidden");
    resetLogin();
}

function resetLogin() {
    $("#resetLogin").hide();
    $("#logincode").blur();
    $("#loginForm .columnright").fadeOut(1000, function() {
        $("#loginForm .columnleft").animate({
            width:'38em'}, function() {
                    $("#users a").show();
                }
            );
        }
    );
    $("#loginname").val('');
    $("#logincode").val('');
}

function chooseUser(id, name) {
    $("#loginname").val(name);
    $("#"+id).addClass('selected');
    $("#users a[id!='" + id + "']").hide();
    $("#loginForm .columnleft").animate({
        width:'12em'}, function() {
            $("#loginForm .columnright").fadeIn(500, function() {
                $("#logincode").focus();
                $("#resetLogin").show();
            });    
        }
    );
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
    var finalc = initial.substr(0, initial.length-1);
    $("#logincode").val(finalc);
}
