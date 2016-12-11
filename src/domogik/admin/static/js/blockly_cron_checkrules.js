// Add A cron check dialog to blockly Field Cron

function createCronCheckDialog(blImage, inputName) {
//    var resultsName = "";
    var blocklyImage = blImage;
    var blocklyElement = blocklyImage.fieldGroup_;
    var inputName = inputName;
    var displayTimeUnit = function (unit) {
        if (unit.toString().length == 1)
            return "0" + unit;
        return unit;
    };

    var timeSelectOption = function (i) {
        return "<option id='" + i + "'>" + displayTimeUnit(i) + "</option>";
    };

    var nextDateList = function (d) {
        if (d instanceof Array) {
            // js date month [0..11]
            var date = new Date(d[0], parseInt(d[1])-1, d[2], d[3], d[4]);
            return "<li class='small'>| " + date.toString() + "</li>";
        }   else {
        return "<li class='small'>| " + d + "</li>";
        };
    };

    var EPHEM_OPTIONS = {
        "@fullmoon": "Full moon",
        "@newmoon": "New moon",
        "@firstquarter": "First quarter",
        "@lastquarter":  "Last quarter",
        "@equinox": "Equinox",
        "@solstice": "Solstice",
        "@dawn": "Dawn",
        "@dusk": "Dusk"
    };

    var SUBSTITUTIONS_OPTIONS = {
        "@yearly": "Yearly",
        "@anually": "Anually",
        "@monthly": "Monthly",
        "@weekly": "Weekly",
        "@daily": "Daily",
        "@midnight": "Midnight",
        "@hourly": "Hourly"
    };

    //create Container
    var cronContainer = $("<div/>", { id: "CronContainer", style: "display:none;width:300px;height:300px;" });
    var mainDiv = $("<div/>", { id: "CronCheckMainDiv"});
    //create tabs content
    var dateN = new Date().toLocaleDateString('en-GB');
    var cronRule = "<div class='panel panel-default'>"+
                "<div class='panel-heading text-center'>"+
                    "<div class='row-fluid'>"+
                        "<h3 style='margin-top: 5px'><span class='label label-info' id='cronTabExp'>No cron rule</span></h3>"+
                    "</div>" +
                    "<div class='row-fluid'>"+
                        "<span id='cronTranslate'>EXPRESSION</span>"+
                    "</div>"+
                "</div>" +
                "<div class='panel-body'>"+
                    "<div class='row'>"+
                        "<div class='col-sm-3'>"+
                            "<label for='datepicker1'>Test date</label>"+
                            "<div class='input-group'>"+
                                "<input type='text' class='form-control input-sm' id='datepicker1' value="+dateN+">"+
                            "</div>"+
                        "</div>"+
                        "<div class='col-sm-2'>"+
                            "<label for='AtHours'>hour</label>"+
                            "<div class='input-group'>"+
                                "<select id='AtHours' class='form-control input-sm hours'></select>" +
                            "</div>"+
                        "</div>"+
                        "<div class='col-sm-2'>"+
                            "<label for='AtMinutes'>minute</label>"+
                            "<div class='input-group'>"+
                                "<select id='AtMinutes' class='form-control input-sm minutes'></select>"+
                            "</div>"+
                        "</div>"+
                        "<div class='col-sm-5 text-center'>"+
                            "<p id='testNowResult' class='bg-warning'>At now : Not Tested</p>"+
                            "<button type='button' class='btn btn-primary' id='btchekcrondate'>"+
                                "<span class='glyphicon glyphicon-check' aria-hidden='true'></span> Test date"+
                            "</button>"+
                            "<p id='testDateResult' class='bg-warning'>At date : Not Tested</p>"+
                        "</div>"+
                    "</div>"+
                    "<div class='row' style='margin-top: 10px;'>"+
                         "<STYLE type='text/css'>"+
                            "OL { list-style-type: decimal }"+
                        "</STYLE>"+
                        "<form class='form-horizontal'>"+
                            "<div class='form-group'>"+
                                "<label for='nbNextDates' class='col-sm-6 control-label'>Next dates prevision</label>"+
                                "<div class='col-sm-3'>"+
                                    "<select id='nbNextDates' class='form-control input-sm'>"+
                                        "<option>5</option>"+
                                        "<option>10</option>"+
                                        "<option>20</option>"+
                                        "<option>30</option>"+
                                    "</select>"+
                                "</div>"+
                            "</div>"+
                        "</form>"+
                            "<ol class='pre-scrollable' id='listnextdates'>"+
                            "</ol>"+
                    "</div>"+
                "</div>"+
            "</div>";
    $(mainDiv).append(cronRule);
    var container = $("<div/>", { "class": "container-fluid", "style": "margin-top: 10px" });
    var row = $("<div/>", { "class": "row-fluid" });
    var span12 = $("<div/>", { "class": "span12" });
    var tabContent = $("<div/>", { "class": "tab-content" });

    $(container).appendTo(mainDiv);
    $(cronContainer).append(mainDiv);

    this.openPopover = function() {
    };

    var fillDataOfMinutesAndHoursSelectOptions = function () {
        for (var i = 0; i < 60; i++) {
            if (i < 24) {
                $(".hours").each(function () { $(this).append(timeSelectOption(i)); });
            }
            $(".minutes").each(function () { $(this).append(timeSelectOption(i)); });
        };
    };
    $(blocklyElement).attr("data-toggle", "popover");
    $(blocklyElement).popover({
        html: true,
        content: function () {
            return $(mainDiv).html();
        },
        template: '<div class="popover" style="max-width:600px !important; width:600px"><div class="arrow"></div><div class="popover-inner"><h3 class="popover-title"></h3><div class="popover-content"><p></p></div></div></div>',
        placement: 'bottom'

    });
    $(blocklyElement).on('shown.bs.popover', function () {
        var dial = $(".popover");
        dial.appendTo('body');
        var pos = $(this).position();
        var w = dial.width();
        $("#cronTabExp").text(blocklyImage.sourceBlock_.getFieldValue(inputName));
        $("#cronTranslate").text(blocklyImage.sourceBlock_.tooltip);
        dial.css({top: pos.top+25, left: pos.left-(w/2)+12, position:'absolute'});
        $('#datepicker1').datepicker({
            format : "dd/mm/yyyy"
            });
        $('.datepicker').css({"z-index": 2000, "width": "300px"});
        fillDataOfMinutesAndHoursSelectOptions();
        $("#btchekcrondate").click(function() {
            var dateC = $('#datepicker1').val().split('/');
            dateC = dateC[2]+','+dateC[1]+','+dateC[0]+','+$('#AtHours').val() +',' + $('#AtMinutes').val()
            $.getJSON('/scenario/cronruletest/checkdate', {cronrule:$("#cronTabExp").text(), date:dateC}, function(data, result) {
                if (result == "error" || data.content.error != "") {
                    new PNotify({
                        type: 'error',
                        title: 'Fail check date',
                        text: data.content.error,
                        delay: 6000
                    });
                    $("#testNowResult").text('Bad cron expression: ').removeClass().addClass('bg-danger');
                    $("#testDateResult").html(data.content.error).removeClass().addClass('bg-danger');
                } else {
                    var dateC = $('#datepicker1').val() + '<br>at '+$('#AtHours').val() +'h ' + $('#AtMinutes').val()+'mn'
                    $("#testNowResult").text('Triggered for now : '+data.content.result.now);
                    if (data.content.result.now) {$("#testNowResult").removeClass().addClass('bg-success');
                    } else {$("#testNowResult").removeClass().addClass('bg-warning');};
                    $("#testDateResult").html('Triggered for '+dateC+' : '+data.content.result.date);
                    if (data.content.result.date) {$("#testDateResult").removeClass().addClass('bg-success');
                    } else {$("#testDateResult").removeClass().addClass('bg-warning');};
                };
            });
        });
        $("#nbNextDates").change(function() {
            var nb = $("#nbNextDates").val();
            if ( $("#cronTabExp").text() in EPHEM_OPTIONS) {
                var dateN = new Date(); // js date month [0..11]
                var dateC = dateN.getFullYear()+','+parseInt(dateN.getMonth()+1)+','+dateN.getDate()+','+dateN.getHours()+','+dateN.getMinutes();
                $.getJSON('/scenario/cronruletest/getephemdate', {cronrule:$("#cronTabExp").text(), date:dateC, number:nb}, function(data, result) {
                    if (result == "error" || data.content.error != "") {
                        new PNotify({
                            type: 'error',
                            title: 'Fail check date',
                            text: data.content.error,
                            delay: 6000
                        });
                    } else {
                        $("#listnextdates").empty()
                        if (data.content.result.dates != 0) {
                            for (var i = 0; i < data.content.result.dates.length; i++) {
                                $("#listnextdates").each(function () { $(this).append(nextDateList(data.content.result.dates[i])); });
                            };
                        } else {
                            $("#listnextdates").each(function () { $(this).append(nextDateList("Too complex, can't calculate next date"));});
                        };
                    };
                });
            } else {
                later.date.localTime()
                var s = later.parse.cron($("#cronTabExp").text());
                var dates = later.schedule(s).next(nb);
                $("#listnextdates").empty()
                if (dates != 0) {
                    for (var i = 0; i < dates.length; i++) {
                        $("#listnextdates").each(function () { $(this).append(nextDateList(dates[i])); });
                    };
                } else if (s.exceptions.length != 0) {
                    $("#listnextdates").each(function () { $(this).append(nextDateList("Error, can't calculate next date"));});
                } else {
                    $("#listnextdates").each(function () { $(this).append(nextDateList("There no next date"));});
                };
            };
        });
        if (blocklyImage.sourceBlock_.cron_valid) {
            $("#nbNextDates").trigger("change");
        } else {
            $("#nbNextDates").attr('disabled',true)
            $("#cronTabExp").removeClass('label-info').addClass('label-danger');
        };
    });
    $(blocklyElement).on('hidden.bs.popover', function () {
        $('.datepicker').remove();
    });
    blocklyImage.clickEventListener(blocklyImage.imageElement_, this.openPopover);
    return;
};

$('body').on('click', function (e) {
    $('[data-toggle="popover"]').each(function () {
        //the 'is' for buttons that trigger popups
        //the 'has' for icons within a button that triggers a popup
        if (!$(this).is(e.target) && $(this).has(e.target).length === 0 && $('.popover').has(e.target).length === 0) {
            $(this).popover('hide');
        }
    });
});
