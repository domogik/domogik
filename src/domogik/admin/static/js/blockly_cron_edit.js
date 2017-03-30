// Globals constant
CRON_GENERAL = 'General';
CRON_D_MONTH = 'DayOfMonth';
CRON_D_WEEK = 'DayOfWeek';
var todoo = "\nActually Domogik not handle personnal place, wait for next release ;)"
var EPHEM_TRANLATION = {
    "@fullmoon": "At each full moon from Brussels."+todoo ,
    "@newmoon": "At each new moon from Brussels."+todoo ,
    "@firstquarter": "At each first moon quarter from Brussels."+todoo ,
    "@lastquarter":  "At each last moon quarter from Brussels."+todoo ,
    "@equinox": "At each equinox from northern hemisphere."+todoo ,
    "@solstice": "At each solstice from northern hemisphere."+todoo ,
    "@dawn": "At each dawn from Brussels."+todoo ,
    "@dusk": "At each dusk from Brussels."+todoo
};

var PREDEFINED_TRANLATION = {
    "@yearly": "At 00h 00mn of all 1st january.",
    "@anually": "At 00h 00mn of all 1st january.",
    "@monthly": "At 00h 00mn on 1st day of all months.",
    "@weekly": "At 00h 00mn on Sunday.",
    "@daily": "At 00h 00mn on all days.",
    "@midnight": "At 00h 00mn on all days.",
    "@hourly": "At all 00mn."
};

function cron_generalValidation(exp){
	return /^[\d,\-\*\/]+$/.test(exp);
};
function cron_dayOfMonthValidation(exp){
	return /^[\d,\-\*\/LW\?]+$/.test(exp);
};
function cron_dayOfWeekValidation(exp){
	return /^[\d,\-\*\/L#\?]+$/.test(exp);
};

function valideNumRange(m, range) {
    try {
        parseInt(m);
    } catch (err) {return false;};
    return (m >= range[0] && m <= range[1]);
};

function getMsgFieldOOR(field, range,value) {
    return "Error in field '"+field+"' value ("+value+") out of range "+range[0]+" to "+range[1];
};

function CronType(sChar){
    this.specChar= sChar;
};

var NONE = new CronType('');
var NOSPECIFIC = new CronType('?');
var EVERY = new CronType('*');
var FROMTO = new CronType('-');
var EACH = new CronType('/');
var AT = new CronType('');
var ATEACH = new CronType('/');
var FROMTOEACH = new CronType('-');
var LAST = new CronType('L')
var WEEK = new CronType('W');
var NTHDAY = new CronType('#');

function cronPart(crontype,values){
    this.crontype = crontype;
    this.values = values;
};

function cronPart_Parse(str,strType){
	if(strType == CRON_GENERAL) {
		if(!cron_generalValidation(str)){
			return null;
		};
    } else if(strType == CRON_D_MONTH) {
		if(!cron_dayOfMonthValidation(str)){
			return null;
		}
	} else if(strType == CRON_D_WEEK) {
		if(!cron_dayOfWeekValidation(str)){
			return null;
		};
	};

    if (str=='?'){
        return new cronPart(NOSPECIFIC);
    } else if (str=='*'){
        return new cronPart(EVERY);
    } else if (/^\d+(,\d+)*$/.test(str)){
        nums = str.split(',');
        return new cronPart(AT,nums);
    } else if (/^\d+\/\d+$/.test(str)){
        nums = str.split('/');
        return new cronPart(ATEACH,nums);
    } else if( /^\d+\-\d+$/.test(str)){
        nums = str.split('-');
        return new cronPart(FROMTO,nums);
    } else if ( /^\d+\-\d+\/\d+$/.test(str)){
        nums = str.split('-');
        nums2 =nums[1].split('/');
        return new cronPart(FROMTOEACH,[nums[0],nums2[0]],nums2[1]);
    } else if('L'==str){
    	return new cronPart(LAST);
    } else if('W'==str){
    	return new cronPart(WEEK);
    } else if( /^\d+\#\d+$/.test(str)){
        nums = str.split('#');
    	return new cronPart(NTHDAY, nums);
    } else{
        return null;
    };
};

var CRON_FIELD_DATA = {
    "Minute": {
        "label": "Minute",
        "check": ['block_all','block_minute_at','block_minute_from_to','block_minute_inc'],
        "rule" : CRON_GENERAL,
        "range": [0,59],
        "inc" : [1,30]
    },
    "Hour": {
        "label": "Hour",
        "check": ['block_all','block_hour_at','block_hour_from_to','block_hour_inc'],
        "rule" : CRON_GENERAL,
        "range": [0,23],
        "inc" : [1,6]
    },
    "DayOfMonth": {
        "label": "Day of month",
        "check": ['block_all','block_last','block_no_specif','block_day_of_month_at','block_day_of_month_from_to','block_day_of_month_inc','block_day_of_month_near_to_w'],
        "rule" : CRON_D_MONTH,
        "range": [1,31],
        "inc" : [1,15]
    },
    "Month":  {
        "label": "Month",
        "check": ['block_all','block_month_on','block_month_from_to','block_month_inc'],
        "rule" : CRON_GENERAL,
        "range": [1,12],
        "inc" : [1,6]
    },
    "DayOfWeek":  {
        "label": "Day of week",
        "check": ['block_all','block_last','block_no_specif','block_day_w_on','block_day_w_from_to','block_day_w_inc','block_day_w_last_of_month','block_day_w_nth_of_month','block_day_w_w_end'],
        "rule" : CRON_D_WEEK,
        "range": [0,6],
        "inc" : [1,3]
    },
    "Year":  {
        "label": "Year (optional)",
        "check": ['block_all','block_year_in','block_year_from_to','block_year_inc'],
        "rule" : CRON_GENERAL,
        "range": [2016,2200],
        "inc" : [1,100]
    }
}

var EPHEM_OPTIONS = [
    ["Full moon","@fullmoon"],
    ["New moon","@newmoon"],
    ["First quarter","@firstquarter"],
    ["Last quarter","@lastquarter"],
    ["Equinox","@equinox"],
    ["Solstice","@solstice"],
    ["Dawn","@dawn"],
    ["Dusk","@dusk"]
];

var PREDEFINED_OPTIONS = [
    ["Yearly","@yearly"],
    ["Anually","@anually"],
    ["Monthly","@monthly"],
    ["Weekly","@weekly"],
    ["Daily","@daily"],
    ["Midnight","@midnight"],
    ["Hourly","@hourly"]
];
var WEEKDAYS = [["Sunday", "0"], ["Monday", "1"], ["Tuesday", "2"], ["Wednesday", "3"], ["Thursday", "4"], ["Friday", "5"], ["Saturday", "6"]];
var MONTHS = [["January", "1"], ["Frebruary", "2"], ["March", "3"], ["April", "4"], ["May", "5"], ["June", "6"], ["July", "7"], ["August", "8"], ["September", "9"], ["October", "10"], ["November", "11"], ["December", "12"]];

Blockly.Blocks['cron.CronTest'] = {
  init: function() {
    var dropdown = new Blockly.FieldDropdown([["Text", "txt"], ["Blockly", "blockly"],["Ephemeris", "ephem"],["Predefined", "predef"]], function(option) {
        this.sourceBlock_.updateShape_(option);
    });
    this.appendDummyInput()
        .appendField("Trigger on crontab rule ")
        .appendField(dropdown, "crontype")
        .appendField(new Blockly.FieldClickImage('/static/images/icon-cron-invalid.png', 20, 20, '*', createCronCheckDialog),"btCheck");
    this.appendDummyInput("CronExp")
        .appendField("Cron expression :")
        .appendField(new Blockly.FieldTextInput(""), "cron.cron");
    this.setOutput(true);
    this.setColour(120);
    this.setTooltip('');
    this.initDialCheck = false;
    this.cron_old = "";
    this.cron_valid = true;
  },
  mutationToDom: function() {
    var container = document.createElement('mutation');
    var editMode = this.getFieldValue('crontype');
    container.setAttribute('block_input', editMode);
    return container;
  },
  domToMutation: function(xmlElement) {
    var editMode = xmlElement.getAttribute('block_input');
    this.updateShape_(editMode);
  },
  updateShape_: function(editMode) {
    // Add or remove a Value Input.
    var editMode_old = this.getFieldValue('crontype');
    if (editMode == editMode_old) { return;};
    var exp = this.getFieldValue('cron.cron');
    // remove previous input
    switch (editMode_old) {
        case 'txt' :
            this.removeInput('CronExp');
            break;
        case 'blockly' :
            this.removeInput('sampleExp');
            for (input in CRON_FIELD_DATA) {
                var inputBlock = this.getInput(input).connection.targetBlock();
                if (inputBlock) {
                    inputBlock.dispose(true);
                    inputBlock = null;
                };
                this.removeInput(input);
            };
            break;
        case 'ephem' :
            this.removeInput('CronEphem');
            break;
        case 'predef' :
            this.removeInput('CronPredef');
            break;
    };
    // create  new input
    switch (editMode) {
        case 'txt' :
            this.appendDummyInput('CronExp')
                .appendField('Cron expression :')
                .appendField(new Blockly.FieldTextInput(exp), 'cron.cron');
            break;
        case'blockly' :
            this.appendDummyInput('sampleExp')
                .setAlign(Blockly.ALIGN_CENTRE)
                .appendField(exp,'cron.cron');
            for (input in CRON_FIELD_DATA) {
                this.appendValueInput(input)
                    .setCheck(['Array'].concat(CRON_FIELD_DATA[input].check))
                    .appendField(CRON_FIELD_DATA[input].label, CRON_FIELD_DATA[input].label)
                    .setAlign(Blockly.ALIGN_RIGHT);
            };
            this.generateCronBlock_(exp);
            break;
        case 'ephem' :
            this.appendDummyInput('CronEphem')
                .appendField('From Brussels')
                .appendField(new Blockly.FieldDropdown(EPHEM_OPTIONS), "cron.cron")
                .setAlign(Blockly.ALIGN_CENTRE);
            break
        case 'predef':
            this.appendDummyInput('CronPredef')
                .appendField(new Blockly.FieldDropdown(PREDEFINED_OPTIONS), "cron.cron")
                .setAlign(Blockly.ALIGN_CENTRE);
            break;
    };
  },
  onchange: function(changeEvent) {
    if (!this.initDialCheck) {
        createCronCheckDialog(this.getField('btCheck'),"cron.cron");
        this.initDialCheck = true;
    };
    if (this.getFieldValue('crontype') == 'blockly') {
        var badInput = this.validateInputs_()
        if (badInput != "") {
            this.setWarningText('Input that must have a block :\n' + badInput);
        } else {
            this.setWarningText(null);
        };
        for (input in CRON_FIELD_DATA) {
            this.setCheckLists_(input,CRON_FIELD_DATA[input].check);
        };
        this.setCronSample_(this.generateCronExp_());
    } else {
        this.setWarningText(null);
    };
    var exp = this.getFieldValue('cron.cron');
    var trad = "";
    if (exp in EPHEM_TRANLATION) {
        this.cron_valid = true;
        trad = EPHEM_TRANLATION[exp];
    } else if (exp in PREDEFINED_TRANLATION) {
        this.cron_valid = true;
        trad = PREDEFINED_TRANLATION[exp];
    } else {
        trad = "Can't translate cron expression."
        var item = exp.split(' ');
        if (item.length == 5 || item.length == 6) {
            if (exp && this.cron_valid) {
                try {
                    // Add second if year is set
                   var exp2 = exp;
                    if (item.length == 6) {exp2 = "0 "+exp;};
                    trad = cronstrue.toString(exp2, { locale: navigator.language, use24HourTimeFormat:true });
                } catch (err) {};
            };
        };
    };
    this.setTooltip(trad);
    if (this.cron_old != exp) {
        var dateN = new Date(); // js date month [0..11]
        var dateC = dateN.getFullYear()+','+parseInt(dateN.getMonth()+1)+','+dateN.getDate()+','+dateN.getHours()+','+dateN.getMinutes();
        var that = this;
        $.getJSON('/scenario/cronruletest/checkdate', {cronrule:exp, date:dateC}, function(data, result) {
            if (result == "error" || data.content.error != "") {
                that.cron_valid = false;
                $("#bt_save").attr('disabled', true).attr('title', "Save disable, please fix crontab error.");
                that.getField('btCheck').setValue('/static/images/icon-cron-invalid.png');
            } else {
                $("#bt_save").attr('disabled', false).attr('title', "");
                that.cron_valid = true;
                that.getField('btCheck').setValue('/static/images/icon-cron-valid.png');
            };
        });
    };
    this.cron_old = exp;
  },
  setCheckLists_: function(inputName, check) {
    var listCreate = this.getInput(inputName).connection.targetBlock();
    if (listCreate && listCreate.type == "lists_create_with") {
        if (listCreate.nbItems == undefined || listCreate.nbItems != listCreate.inputList.length ||
          listCreate.inputList[0].connection.check_ == null ||
          listCreate.inputList[0].connection.check_.indexOf(check[check.length - 1]) == -1) {
            for (var i=0 ; i < listCreate.inputList.length; i++) {
                listCreate.inputList[i].setCheck(check);
            };
        };
        listCreate.nbItems = listCreate.inputList.length;
    };
  },
  validateInputs_: function() {
    var badInput = "";
    for (input in CRON_FIELD_DATA) {
        if (input != 'Year') {
            if (!this.getInput(input).connection.targetBlock()) {
                badInput += '- '+CRON_FIELD_DATA[input].label+'\n';
                this.setFieldHelper_(input, 'Connect a block in necessary');
            } else {
                this.setFieldHelper_(input, '');
            };
        };
    };
    return badInput;
  },
  setCronSample_ : function(exp) {
    var sampleExp = this.getInput('sampleExp');
    if(sampleExp) {
        for (var i=0; i < sampleExp.fieldRow.length; i++) {
            if (sampleExp.fieldRow[i].name == 'cron.cron') {
                sampleExp.fieldRow[i].setText(exp);
                break;
            };
        };
    };
  },
  generateCronExp_: function() {
    var exp = '';
    var inputBlock;
    this.cron_valid = true;
    for (var input in CRON_FIELD_DATA) {
        inputBlock = this.getInput(input).connection.targetBlock()
        if (input != 'Year') {
            if (inputBlock) {
                if (inputBlock.type == 'lists_create_with') {
                    for (var x = 0, input; input = inputBlock.inputList[x]; x++) {
                        var item = input.connection.targetBlock();
                        if (item) {
                            exp += item.formatValue_() + ',';
                        } else {
                            this.cron_valid = false;
//                            return 'Bad cron format ! ('+exp+')';
                            return exp;
                        };
                    };
                    exp = exp.replace(/,$/, " ");
                } else {
                    exp += inputBlock.formatValue_() + ' ';
                };
            } else {
                this.cron_valid = false;
//                            return 'Bad cron format ! ('+exp+')';
                return exp;
            };
        } else {
            if (inputBlock) {
                if (inputBlock.type == 'lists_create_with') {
                    for (var x = 0, input; input = inputBlock.inputList[x]; x++) {
                        var item = input.connection.targetBlock();
                        if (item) {
                            exp += item.formatValue_() + ',';
                        } else {
                            this.cron_valid = false;
//                            return 'Bad cron format ! ('+exp+')';
                            return exp;
                        };
                    };
                    exp = exp.replace(/,$/, "");
                } else {
                    exp += inputBlock.formatValue_();
                };
            };
        };
    };
    return exp.replace(/ $/, "");
  },
  generateCronBlock_: function(exp) {
      var item = exp.split(' ');
      var result = ""
      var expI, error;
      if (item.length == 5 || item.length == 6) {
        this.setFieldHelper_('Minute', this.generateCronInput_(item[0], 'Minute', this.MinuteToBlock_), true);
        this.setFieldHelper_('Hour', this.generateCronInput_(item[1], 'Hour', this.HourToBlock_), true);
        this.setFieldHelper_('DayOfMonth', this.generateCronInput_(item[2], 'DayOfMonth', this.DayOfMonthToBlock_), true);
        this.setFieldHelper_('Month', this.generateCronInput_(item[3], 'Month', this.MonthToBlock_), true);
        this.setFieldHelper_('DayOfWeek', this.generateCronInput_(item[4], 'DayOfWeek', this.DayOfWeekToBlock_), true);
        if (item.length == 6) {
            this.setFieldHelper_('Year', this.generateCronInput_(item[5], 'Year', this.YearToBlock_), true);
        };
    };
  },
  createBlockList_: function(nbItem) {
    var nBlock = this.workspace.newBlock('lists_create_with');
    if (nbItem != nBlock.inputList.length) {
        // handle mutations
        var mut = document.createElement('div');
        mut.setAttribute('items', nbItem)
        nBlock.domToMutation(mut);
    };
    return nBlock;
  },
  getValue : function() {
        return this.getFieldValue('cron.cron')
  },
  setFieldHelper_: function(input, text, notify) {
    this.getField(CRON_FIELD_DATA[input].label).setTooltip(text);
    if (text != "") {
        if (notify) {
            new PNotify({
                type: 'error',
                title: 'Field '+input+' error',
                text: text,
                delay: 6000
            });
        };
        $(this.getField(CRON_FIELD_DATA[input].label).textElement_).css({'fill': 'red'});
    } else {
        $(this.getField(CRON_FIELD_DATA[input].label).textElement_).css({'fill': 'white'});
    };
  },
  // Cron expression to block
  generateCronInput_: function(item, inputName, constructorBlock){
    var subItem = item.split(',');
    var result = "";
    if (subItem.length > 1) {
        var lBlock = this.createBlockList_(subItem.length);
        this.getInput(inputName).connection.connect(lBlock.outputConnection);
        for (var sb=0; sb < subItem.length; sb++) {
            expI = cronPart_Parse(subItem[sb], CRON_FIELD_DATA[inputName].rule);
            error = constructorBlock(expI, lBlock.inputList[sb].connection);
            if (error != "") {
              result+= error+"\n";
            };
        };
        lBlock.initSvg();
        lBlock.render();
    } else {
        expI = cronPart_Parse(item, CRON_FIELD_DATA[inputName].rule);
        error = constructorBlock(expI, this.getInput(inputName).connection);
        if (error != "") {
          result = error+"\n";
        };
    };
    return result;
  },
  MinuteToBlock_: function(exp, connectTo) {
    var error = "";
    if (exp) {
        var range = CRON_FIELD_DATA['Minute'].range;
        var rInc = CRON_FIELD_DATA['Minute'].inc;
        var nBlock = null;
        if (exp.crontype.specChar == '*'){
          var nBlock = this.workspace.newBlock('block_all');
        } else if (exp.crontype.specChar == '-') {
            if (!valideNumRange(exp.values[0], range)) { return getMsgFieldOOR('from', range, exp.values[0]);};
            if (!valideNumRange(exp.values[1], range)) { return getMsgFieldOOR('to', range, exp.values[1]);};
            var nBlock = this.workspace.newBlock('block_minute_from_to');
            nBlock.setFieldValue(exp.values[0], 'from');
            nBlock.setFieldValue(exp.values[1], 'to');
        } else if (exp.crontype.specChar == '/') {
            var nBlock = this.workspace.newBlock('block_minute_inc');
            if (!valideNumRange(exp.values[0], range)) { return getMsgFieldOOR('start', range, exp.values[0]);};
            if (!valideNumRange(exp.values[1], rInc)) { return getMsgFieldOOR('inc',rInc, exp.values[1]);};
            nBlock.setFieldValue(exp.values[0], 'start');
            nBlock.setFieldValue(exp.values[1], 'inc');
        } else if (exp.crontype.specChar == '') {
            if (!valideNumRange(exp.values[0],range)) { return getMsgFieldOOR('minute',range, exp.values[0]);};
            var nBlock = this.workspace.newBlock('block_minute_at');
            nBlock.setFieldValue(exp.values[0], 'minute');
        };
        if (nBlock) {
            nBlock.initSvg();
            connectTo.connect(nBlock.outputConnection);
            nBlock.render();
        };
    } else { error = "No minute part"; };
    return error;
  },
  HourToBlock_: function(exp, connectTo) {
    var error = "";
    if (exp) {
        var range = CRON_FIELD_DATA['Hour'].range;
        var rInc = CRON_FIELD_DATA['Hour'].inc;
        var nBlock = null;
        if (exp.crontype.specChar == '*'){
          var nBlock = this.workspace.newBlock('block_all');
        } else if (exp.crontype.specChar == '-') {
            if (!valideNumRange(exp.values[0], range)) { return getMsgFieldOOR('from', range, exp.values[0]);};
            if (!valideNumRange(exp.values[1], range)) { return getMsgFieldOOR('to', range, exp.values[1]);};
            var nBlock = this.workspace.newBlock('block_hour_from_to');
            nBlock.setFieldValue(exp.values[0], 'from');
            nBlock.setFieldValue(exp.values[1], 'to');
        } else if (exp.crontype.specChar == '/') {
            if (!valideNumRange(exp.values[0], range)) { return getMsgFieldOOR('start', range, exp.values[0]);};
            if (!valideNumRange(exp.values[1], rInc)) { return getMsgFieldOOR('inc',rInc, exp.values[1]);};
            var nBlock = this.workspace.newBlock('block_hour_inc');
            nBlock.setFieldValue(exp.values[0], 'start');
            nBlock.setFieldValue(exp.values[1], 'inc');
        } else if (exp.crontype.specChar == '') {
            if (!valideNumRange(exp.values[0],range)) { return getMsgFieldOOR('hour',range, exp.values[0]);};
            var nBlock = this.workspace.newBlock('block_hour_at');
            nBlock.setFieldValue(exp.values[0], 'hour');
        };
        if (nBlock) {
            nBlock.initSvg();
            connectTo.connect(nBlock.outputConnection);
            nBlock.render();
        };
    } else { error = "No hour part"; };
    return error;
  },
  DayOfMonthToBlock_: function(exp, connectTo) {
    var error = "";
    if (exp) {
        var range = CRON_FIELD_DATA['DayOfMonth'].range;
        var rInc = CRON_FIELD_DATA['DayOfMonth'].inc;
        var nBlock = null;
        if (exp.crontype.specChar == '*'){
          var nBlock = this.workspace.newBlock('block_all');
        } else if (exp.crontype.specChar == '-') {
            var nBlock = this.workspace.newBlock('block_day_of_month_from_to');
            if (!valideNumRange(exp.values[0], range)) { return getMsgFieldOOR('from', range, exp.values[0]);};
            if (!valideNumRange(exp.values[1], range)) { return getMsgFieldOOR('to', range, exp.values[1]);};
            nBlock.setFieldValue(exp.values[0], 'from');
            nBlock.setFieldValue(exp.values[1], 'to');
        } else if (exp.crontype.specChar == '/') {
            var nBlock = this.workspace.newBlock('block_day_of_month_inc');
            if (!valideNumRange(exp.values[0], range)) { return getMsgFieldOOR('start', range, exp.values[0]);};
            if (!valideNumRange(exp.values[1], rInc)) { return getMsgFieldOOR('inc',rInc, exp.values[1]);};
            nBlock.setFieldValue(exp.values[0], 'start');
            nBlock.setFieldValue(exp.values[1], 'inc');
        } else if (exp.crontype.specChar == 'L') {
            var nBlock = this.workspace.newBlock('block_last');
        } else if (exp.crontype.specChar == 'W') {
            if (!valideNumRange(exp.values[0],range)) { return getMsgFieldOOR('day of month',range, exp.values[0]);};
            var nBlock = this.workspace.newBlock('block_day_of_month_near_to_w');
            nBlock.setFieldValue(exp.values[0], 'day_m');
        } else if (exp.crontype.specChar == '?') {
            var nBlock = this.workspace.newBlock('block_no_specif');
        } else if (exp.crontype.specChar == '') {
            if (!valideNumRange(exp.values[0],range)) { return getMsgFieldOOR('day of month',range, exp.values[0]);};
            var nBlock = this.workspace.newBlock('block_day_of_month_at');
            nBlock.setFieldValue(exp.values[0], 'day_m');
        };
        if (nBlock) {
            nBlock.initSvg();
            connectTo.connect(nBlock.outputConnection);
            nBlock.render();
        };
    } else { error = "No day of month part"; };
    return error;
  },
  MonthToBlock_: function(exp, connectTo) {
    var error = "";
    if (exp) {
        var range = CRON_FIELD_DATA['Month'].range;
        var rInc = CRON_FIELD_DATA['Month'].inc;
        var nBlock = null;
        if (exp.crontype.specChar == '*'){
          var nBlock = this.workspace.newBlock('block_all');
        } else if (exp.crontype.specChar == '-') {
            var nBlock = this.workspace.newBlock('block_month_from_to');
            if (!valideNumRange(exp.values[0], range)) { return getMsgFieldOOR('from', range, exp.values[0]);};
            if (!valideNumRange(exp.values[1], range)) { return getMsgFieldOOR('to', range, exp.values[1]);};
            nBlock.setFieldValue(exp.values[0], 'from');
            nBlock.setFieldValue(exp.values[1], 'to');
        } else if (exp.crontype.specChar == '/') {
            var nBlock = this.workspace.newBlock('block_month_inc');
            if (!valideNumRange(exp.values[0], range)) { return getMsgFieldOOR('start', range, exp.values[0]);};
            if (!valideNumRange(exp.values[1], rInc)) { return getMsgFieldOOR('inc',rInc, exp.values[1]);};
            nBlock.setFieldValue(exp.values[0], 'start');
            nBlock.setFieldValue(exp.values[1], 'inc');
        } else if (exp.crontype.specChar == '') {
            if (!valideNumRange(exp.values[0],range)) { return getMsgFieldOOR('month',range, exp.values[0]);};
            var nBlock = this.workspace.newBlock('block_month_on');
            nBlock.setFieldValue(exp.values[0], 'month');
        };
        if (nBlock) {
            nBlock.initSvg();
            connectTo.connect(nBlock.outputConnection);
            nBlock.render();
        };
    } else { error = "No month part"; };
    return error;
  },
  DayOfWeekToBlock_: function(exp, connectTo) {
    var error = "";
    if (exp) {
        var range = CRON_FIELD_DATA['DayOfWeek'].range;
        var rInc = CRON_FIELD_DATA['DayOfWeek'].inc;
        var nBlock = null;
        if (exp.crontype.specChar == '*'){
          var nBlock = this.workspace.newBlock('block_all');
        } else if (exp.crontype.specChar == '-') {
            var nBlock = this.workspace.newBlock('block_day_w_from_to');
            if (!valideNumRange(exp.values[0], range)) { return getMsgFieldOOR('from', range, exp.values[0]);};
            if (!valideNumRange(exp.values[1], range)) { return getMsgFieldOOR('to', range, exp.values[1]);};
            nBlock.setFieldValue(exp.values[0], 'from');
            nBlock.setFieldValue(exp.values[1], 'to');
        } else if (exp.crontype.specChar == '/') {
            var nBlock = this.workspace.newBlock('block_day_w_inc');
            if (!valideNumRange(exp.values[0], range)) { return getMsgFieldOOR('start', range, exp.values[0]);};
            if (!valideNumRange(exp.values[1], rInc)) { return getMsgFieldOOR('inc',rInc, exp.values[1]);};
            nBlock.setFieldValue(exp.values[0], 'start');
            nBlock.setFieldValue(exp.values[1], 'inc');
        } else if (exp.crontype.specChar == '?') {
            var nBlock = this.workspace.newBlock('block_no_specif');
        } else if (exp.crontype.specChar == 'L') {
            if (exp.values.length == 0) {
                var nBlock = this.workspace.newBlock('block_last');
            } else {
                var nBlock = this.workspace.newBlock('block_day_w_last_of_month');
                if (!valideNumRange(exp.values[0],range)) { return getMsgFieldOOR('week day', range, exp.values[0]);};
                nBlock.setFieldValue(exp.values[0], 'day_w');
            };
        } else if (exp.crontype.specChar == '#') {
            var nBlock = this.workspace.newBlock('block_day_w_nth_of_month');
            if (!valideNumRange(exp.values[0], range)) { return getMsgFieldOOR('week day',range, exp.values[0]);};
            if (!valideNumRange(exp.values[1], rInc)) { return getMsgFieldOOR('nth day', rInc, exp.values[1]);};
            nBlock.setFieldValue(exp.values[0], 'day_w');
            nBlock.setFieldValue(exp.values[1], 'nth');
        } else if (exp.crontype.specChar == '') {
            var nBlock = this.workspace.newBlock('block_day_w_on');
            if (!valideNumRange(exp.values[0],range)) { return getMsgFieldOOR('week day',range, exp.values[0]);};
            nBlock.setFieldValue(exp.values[0], 'day_w');
        };
        if (nBlock) {
            nBlock.initSvg();
            connectTo.connect(nBlock.outputConnection);
            nBlock.render();
        };
    } else { error = "No day of week part"; };
    return error;
  },
  YearToBlock_: function(exp, connectTo) {
    var error = "";
    if (exp) {
        var range = CRON_FIELD_DATA['Year'].range;
        var rInc = CRON_FIELD_DATA['Year'].inc;
        var nBlock = null;
        if (exp.crontype.specChar == '*'){
          var nBlock = this.workspace.newBlock('block_all');
        } else if (exp.crontype.specChar == '-') {
            var nBlock = this.workspace.newBlock('block_year_from_to');
            if (!valideNumRange(exp.values[0], range)) { return getMsgFieldOOR('from', range, exp.values[0]);};
            if (!valideNumRange(exp.values[1], range)) { return getMsgFieldOOR('to', range, exp.values[1]);};
            nBlock.setFieldValue(exp.values[0], 'from');
            nBlock.setFieldValue(exp.values[1], 'to');
        } else if (exp.crontype.specChar == '/') {
            var nBlock = this.workspace.newBlock('block_year_inc');
            if (!valideNumRange(exp.values[0], range)) { return getMsgFieldOOR('start', range, exp.values[0]);};
            if (!valideNumRange(exp.values[1], rInc)) { return getMsgFieldOOR('inc',rInc, exp.values[1]);};
            nBlock.setFieldValue(exp.values[0], 'start');
            nBlock.setFieldValue(exp.values[1], 'inc');
        } else if (exp.crontype.specChar == '') {
            var nBlock = this.workspace.newBlock('block_year_in');
            if (!valideNumRange(exp.values[1], range)) { return getMsgFieldOOR('year', range, exp.values[0]);};
            nBlock.setFieldValue(exp.values[0], 'year');
        };
        if (nBlock) {
            nBlock.initSvg();
            connectTo.connect(nBlock.outputConnection);
            nBlock.render();
        };
    } else { error = "No year part"; };
    return error;
  }
};

// Options Block
// Generic Block
Blockly.Blocks['block_all'] = {
  init: function() {
    this.appendDummyInput()
        .appendField("All");
    this.setOutput(true, 'block_all');
    this.setColour(330);
    this.setTooltip('Used to select all values within a field. For example, * in the minute field means “every minute”.');
  },
  formatValue_: function() {
      return '*'
  }
};

Blockly.Blocks['block_no_specif'] = {
  init: function() {
    this.appendDummyInput()
        .appendField("No specific");
    this.setOutput(true, 'block_no_specif');
    this.setColour(20);
    this.setTooltip("Used when you need to specify something in one of the two fields in which the character is allowed, but not the other."+
                " For example, if I want my trigger to fire on a particular day of the month (say, the 10th),"+
                " but don’t care what day of the week that happens to be, I would put “10” in the day-of-month field,"+
                " and “?” in the day-of-week field.");
  },
  formatValue_: function() {
      return '?';
  }
};

Blockly.Blocks['block_last'] = {
  init: function() {
    this.appendDummyInput()
        .appendField("Last");
    this.setOutput(true, 'block_last');
    this.setColour(330);
    this.setTooltip("Has different meaning in each of the two fields in which it is allowed."+
                " For example, the value “L” in the day-of-month field means “the last day of the month” - day 31 for January,"+
                " day 28 for February on non-leap years. If used in the day-of-week field by itself, it simply means “7” or “SAT”."+
                " But if used in the day-of-week field after another value, it means “the last xxx day of the month” - for example “6L” means “the last friday of the month”."+
                " You can also specify an offset from the last day of the month, such as “L-3” which would mean the third-to-last day of the calendar month."+
                " When using the ‘L’ option, it is important not to specify lists, or ranges of values, as you’ll get confusing/unexpected results.");
  },
  formatValue_: function() {
      return 'L';
  }
};

Blockly.Blocks['block_empty'] = {
  init: function() {
    this.appendDummyInput()
        .appendField("Empty");
    this.setOutput(true, 'block_empty');
    this.setColour(330);
    this.setTooltip('');
  },
  formatValue_: function() {
      return '';
  }
};

// Block minute
Blockly.Blocks['block_minute_at'] = {
  init: function() {
    this.appendDummyInput()
        .appendField("At")
        .appendField(new Blockly.FieldNumber(0, CRON_FIELD_DATA['Minute'].range[0], CRON_FIELD_DATA['Minute'].range[1]), "minute")
        .appendField("mn");
    this.setOutput(true, 'block_minute_at');
    this.setColour(160);
    this.setTooltip("Used to specify a particular minute. For example, “30” means “at 30 minutes after hour”.");
  },
  formatValue_: function() {
      return this.getFieldValue('minute');
  }
};

Blockly.Blocks['block_minute_from_to'] = {
  init: function() {
    this.appendDummyInput()
        .appendField("From")
        .appendField(new Blockly.FieldNumber(0, CRON_FIELD_DATA['Minute'].range[0], CRON_FIELD_DATA['Minute'].range[1]), "from")
        .appendField("mn");
    this.appendDummyInput()
        .appendField("to")
        .appendField(new Blockly.FieldNumber(0, CRON_FIELD_DATA['Minute'].range[0], CRON_FIELD_DATA['Minute'].range[1]), "to")
        .appendField("mn");
    this.setInputsInline(true);
    this.setOutput(true, 'block_minute_from_to');
    this.setColour(160);
    this.setTooltip('Used to specify ranges. For example, “5-10” means “all minutes between 5 to 10”.');
  },
  formatValue_: function() {
      return this.getFieldValue('from')+'-'+this.getFieldValue('to');
  }
};

Blockly.Blocks['block_minute_inc'] = {
  init: function() {
    this.appendDummyInput()
        .appendField("Starting from")
        .appendField(new Blockly.FieldNumber(0, CRON_FIELD_DATA['Minute'].range[0], CRON_FIELD_DATA['Minute'].range[1]), "start")
        .appendField("mn");
    this.appendDummyInput()
        .appendField("every")
        .appendField(new Blockly.FieldNumber(0, CRON_FIELD_DATA['Minute'].inc[0], CRON_FIELD_DATA['Minute'].inc[1]), "inc")
        .appendField("mn");
    this.setInputsInline(true);
    this.setOutput(true, 'block_minute_inc');
    this.setColour(160);
    this.setTooltip("Used to specify increments. For example, “0/15” means “the minutes 0, 15, 30, and 45”.");
  },
  formatValue_: function() {
      return this.getFieldValue('start')+'/'+this.getFieldValue('inc')
  }
};

// Block hour
Blockly.Blocks['block_hour_at'] = {
  init: function() {
    this.appendDummyInput()
        .appendField("At")
        .appendField(new Blockly.FieldNumber(0, CRON_FIELD_DATA['Hour'].range[0], CRON_FIELD_DATA['Hour'].range[1]), "hour")
        .appendField("h");
    this.setOutput(true, 'block_hour_at');
    this.setColour(230);
    this.setTooltip("Used to specify a particular hour. For example, “10” means “at 10 h”.");
  },
  formatValue_: function() {
      return this.getFieldValue('hour');
  }
};

Blockly.Blocks['block_hour_from_to'] = {
  init: function() {
    this.appendDummyInput()
        .appendField("From")
        .appendField(new Blockly.FieldNumber(0, CRON_FIELD_DATA['Hour'].range[0], CRON_FIELD_DATA['Hour'].range[1]), "from")
        .appendField("h");
    this.appendDummyInput()
        .appendField("to")
        .appendField(new Blockly.FieldNumber(0, CRON_FIELD_DATA['Hour'].range[0], CRON_FIELD_DATA['Hour'].range[1]), "to")
        .appendField("h");
    this.setInputsInline(true);
    this.setOutput(true, 'block_hour_from_to');
    this.setColour(230);
    this.setTooltip("Used to specify ranges. For example, “10-12” means “the hours 10, 11 and 12”.");
  },
  formatValue_: function() {
      return this.getFieldValue('from')+'-'+this.getFieldValue('to');
  }
};

Blockly.Blocks['block_hour_inc'] = {
  init: function() {
    this.appendDummyInput()
        .appendField("Starting from")
        .appendField(new Blockly.FieldNumber(0, CRON_FIELD_DATA['Hour'].range[0], CRON_FIELD_DATA['Hour'].range[1]), "start")
        .appendField("h");
    this.appendDummyInput()
        .appendField("every")
        .appendField(new Blockly.FieldNumber(0, CRON_FIELD_DATA['Hour'].inc[0], CRON_FIELD_DATA['Hour'].inc[1]), "inc")
        .appendField("h");
    this.setInputsInline(true);
    this.setOutput(true, 'block_hour_inc');
    this.setColour(230);
    this.setTooltip("Used to specify increments. For example, “2/5” means “the hours 2, 7, 12, 15, 18, and 23.");
  },
  formatValue_: function() {
      return this.getFieldValue('start')+'/'+this.getFieldValue('inc');
  }
};

// Block Day of month
Blockly.Blocks['block_day_of_month_at'] = {
  init: function() {
    this.appendDummyInput()
        .appendField("At")
        .appendField(new Blockly.FieldNumber(1, CRON_FIELD_DATA['DayOfMonth'].range[0], CRON_FIELD_DATA['DayOfMonth'].range[1]), "day_m")
        .appendField("of month");
    this.setOutput(true, 'block_day_of_month_at');
    this.setColour(65);
    this.setTooltip("Used to specify a particular day of the month. For example, “15” means “the 15th day of the month”.");
  },
  formatValue_: function() {
      return this.getFieldValue('day_m');
  }
};

Blockly.Blocks['block_day_of_month_from_to'] = {
  init: function() {
    this.appendDummyInput()
        .appendField("From")
        .appendField(new Blockly.FieldNumber(1, CRON_FIELD_DATA['DayOfMonth'].range[0], CRON_FIELD_DATA['DayOfMonth'].range[1]), "from");
    this.appendDummyInput()
        .appendField("to")
        .appendField(new Blockly.FieldNumber(1, CRON_FIELD_DATA['DayOfMonth'].range[0], CRON_FIELD_DATA['DayOfMonth'].range[1]), "to")
        .appendField("of the month");
    this.setInputsInline(true);
    this.setOutput(true, 'block_day_of_month_from_to');
    this.setColour(65);
    this.setTooltip("Used to specify ranges. For example, “5-25” means “all day of month between 5th to 25th”.");
  },
  formatValue_: function() {
      return this.getFieldValue('from')+'-'+this.getFieldValue('to');
  }
};

Blockly.Blocks['block_day_of_month_inc'] = {
  init: function() {
    this.appendDummyInput()
        .appendField("Starting from")
        .appendField(new Blockly.FieldNumber(1, CRON_FIELD_DATA['DayOfMonth'].range[0], CRON_FIELD_DATA['DayOfMonth'].range[1]), "start");
    this.appendDummyInput()
        .appendField("of the month every")
        .appendField(new Blockly.FieldNumber(1, CRON_FIELD_DATA['DayOfMonth'].inc[0], CRON_FIELD_DATA['DayOfMonth'].inc[1]), "inc")
        .appendField("day");
    this.setInputsInline(true);
    this.setOutput(true, 'block_day_of_month_inc');
    this.setColour(65);
    this.setTooltip("Used to specify increments. For example, “1/3” means “fire every 3 days starting on the first day of the month”.");
  },
  formatValue_: function() {
      return this.getFieldValue('start')+'/'+this.getFieldValue('inc');
  }
};

Blockly.Blocks['block_day_of_month_near_to_w'] = {
  init: function() {
    this.appendDummyInput()
        .appendField("The nearest weekday to the")
        .appendField(new Blockly.FieldNumber(1, CRON_FIELD_DATA['DayOfMonth'].range[0], CRON_FIELD_DATA['DayOfMonth'].range[1]), "day_m")
        .appendField("of the month");
    this.setInputsInline(true);
    this.setOutput(true, 'block_day_of_month_near_to_w');
    this.setColour(65);
    this.setTooltip("Used to specify the weekday (Monday-Friday) nearest the given day."+
                " As an example, if you were to specify “15W” as the value for the day-of-month field,"+
                " the meaning is: “the nearest weekday to the 15th of the month”. So if the 15th is a Saturday,"+
                " the trigger will fire on Friday the 14th. If the 15th is a Sunday, the trigger will fire on Monday the 16th."+
                " If the 15th is a Tuesday, then it will fire on Tuesday the 15th."+
                " However if you specify “1W” as the value for day-of-month, and the 1st is a Saturday, the trigger will fire on Monday the 3rd,"+
                " as it will not ‘jump’ over the boundary of a month’s days. The ‘W’ character can only be specified when the day-of-month is a single day, not a range or list of days.\n"+
                "The 'L' and 'W' characters can also be combined in the day-of-month field to yield 'LW', which translates to “last weekday of the month”.");
  },
  formatValue_: function() {
      return this.getFieldValue('day_m')+'W';
  }
};

// Block month
Blockly.Blocks['block_month_on'] = {
  init: function() {
    this.appendDummyInput()
        .appendField("On")
        .appendField(new Blockly.FieldDropdown(MONTHS), "month");
    this.setInputsInline(true);
    this.setOutput(true, 'block_month_on');
    this.setColour(45);
    this.setTooltip("Used to specify a particular month. For example, “7” means “july”.");
  },
  formatValue_: function() {
      return this.getFieldValue('month');
  }
};

Blockly.Blocks['block_month_from_to'] = {
  init: function() {
    this.appendDummyInput()
        .appendField("From")
        .appendField(new Blockly.FieldDropdown(MONTHS), "from");
    this.appendDummyInput()
        .appendField("to")
        .appendField(new Blockly.FieldDropdown(MONTHS), "to");
    this.setInputsInline(true);
    this.setOutput(true, 'block_month_from_to');
    this.setColour(45);
    this.setTooltip("Used to specify ranges. For example, “2-6” means “all month between february to june”.");
  },
  formatValue_: function() {
      return this.getFieldValue('from')+'-'+this.getFieldValue('to');
  }
};

Blockly.Blocks['block_month_inc'] = {
  init: function() {
    this.appendDummyInput()
        .appendField("Starting from")
        .appendField(new Blockly.FieldDropdown(MONTHS.slice(0, MONTHS.length -1)), "start");
    this.appendDummyInput()
        .appendField("every")
        .appendField(new Blockly.FieldNumber(1, CRON_FIELD_DATA['Month'].inc[0], CRON_FIELD_DATA['Month'].inc[1]), "inc")
        .appendField("month");
    this.setInputsInline(true);
    this.setOutput(true, 'block_month_inc');
    this.setColour(45);
    this.setTooltip("Used to specify increments. For example, “1/4” means “the month january, may and september”.");
  },
  formatValue_: function() {
      return this.getFieldValue('start')+'/'+this.getFieldValue('inc');
  }
};

// Block day of week
Blockly.Blocks['block_day_w_on'] = {
  init: function() {
    this.appendDummyInput()
        .appendField("On")
        .appendField(new Blockly.FieldDropdown(WEEKDAYS), "day_w");
    this.setInputsInline(true);
    this.setOutput(true, 'block_day_w_on');
    this.setColour(290);
    this.setTooltip("Used to specify a particular day of week. For example, “1” means “monday”.");
  },
  formatValue_: function() {
      return this.getFieldValue('day_w');
  }
};

Blockly.Blocks['block_day_w_from_to'] = {
  init: function() {
    this.appendDummyInput()
        .appendField("From")
        .appendField(new Blockly.FieldDropdown(WEEKDAYS), "from");
    this.appendDummyInput()
        .appendField("to")
        .appendField(new Blockly.FieldDropdown(WEEKDAYS), "to");
    this.setInputsInline(true);
    this.setOutput(true, 'block_day_w_from_to');
    this.setColour(290);
    this.setTooltip("Used to specify ranges. For example, “2-5” means “all day of week between tuesday to friday”.");
  },
  formatValue_: function() {
      return this.getFieldValue('from')+'-'+this.getFieldValue('to');
  }
};

Blockly.Blocks['block_day_w_inc'] = {
  init: function() {
    this.appendDummyInput()
        .appendField("Starting on")
        .appendField(new Blockly.FieldDropdown(WEEKDAYS), "start");
    this.appendDummyInput()
        .appendField("every")
        .appendField(new Blockly.FieldNumber(1, CRON_FIELD_DATA['DayOfWeek'].inc[0], CRON_FIELD_DATA['DayOfWeek'].inc[1]), "inc")
        .appendField("day");
    this.setInputsInline(true);
    this.setOutput(true, 'block_day_w_inc');
    this.setColour(290);
    this.setTooltip("Used to specify increments. For example, “1/2” means “the day of week sunday, tuesday, thursday, and saturday”.");
  },
  formatValue_: function() {
      return this.getFieldValue('start')+'/'+this.getFieldValue('inc');
  }
};

Blockly.Blocks['block_day_w_last_of_month'] = {
  init: function() {
    this.appendDummyInput()
        .appendField("The last")
        .appendField(new Blockly.FieldDropdown(WEEKDAYS), "day_w")
        .appendField("of the month");
    this.setInputsInline(true);
    this.setOutput(true, 'block_day_w_last_of_month');
    this.setColour(290);
    this.setTooltip("Used to specify “the last xxx day of the month” - for example “6L” means “the last friday of the month”.");
  },
  formatValue_: function() {
      return this.getFieldValue('day_w')+'L';
  }
};

Blockly.Blocks['block_day_w_nth_of_month'] = {
  init: function() {
    this.appendDummyInput()
        .appendField("The")
        .appendField(new Blockly.FieldDropdown([["1st", "1"], ["2nd", "2"], ["3rd", "3"], ["4th", "4"], ["5th", "5"]]), "nth");
    this.appendDummyInput()
        .appendField(new Blockly.FieldDropdown(WEEKDAYS), "day_w")
        .appendField("of the month");
    this.setInputsInline(true);
    this.setOutput(true, 'block_day_w_nth_of_month');
    this.setColour(290);
    this.setTooltip("Used to specify “the nth” XXX day of the month."+
                " For example, the value of “6#3” in the day-of-week field means “the third Friday of the month” (day 6 = Friday and “#3” = the 3rd one in the month)."+
                " Other examples: “2#1” = the first Monday of the month and “4#5” = the fifth Wednesday of the month."+
                " Note that if you specify “#5” and there is not 5 of the given day-of-week in the month, then no firing will occur that month.");
  },
  formatValue_: function() {
      return this.getFieldValue('day_w')+'#'+this.getFieldValue('nth');
  }
};

Blockly.Blocks['block_day_w_w_end'] = {
  init: function() {
    this.appendDummyInput()
        .appendField("On weekend");
    this.setInputsInline(true);
    this.setOutput(true, 'block_day_w_w_end');
    this.setColour(290);
    this.setTooltip("Used to specify weekend day “saturday and sunday”.");
  },
  formatValue_: function() {
      return '0,6';
  }
};

// Block year
Blockly.Blocks['block_year_in'] = {
  init: function() {
    this.appendDummyInput()
        .appendField("In")
        .appendField(new Blockly.FieldNumber(0, CRON_FIELD_DATA['Year'].range[0], CRON_FIELD_DATA['Year'].range[1]), "year");
    this.setOutput(true, 'block_year_in');
    this.setColour(100);
    this.setTooltip("Used to specify a particular year. For example, “2017” means “in 2017”.");
  },
  formatValue_: function() {
      return this.getFieldValue('year');
  }
};

Blockly.Blocks['block_year_from_to'] = {
  init: function() {
    this.appendDummyInput()
        .appendField("From")
        .appendField(new Blockly.FieldNumber(0, CRON_FIELD_DATA['Year'].range[0], CRON_FIELD_DATA['Year'].range[1]), "from");
    this.appendDummyInput()
        .appendField("to")
        .appendField(new Blockly.FieldNumber(0, CRON_FIELD_DATA['Year'].range[0], CRON_FIELD_DATA['Year'].range[1]), "to");
    this.setInputsInline(true);
    this.setOutput(true, 'block_year_from_to');
    this.setColour(100);
    this.setTooltip("Used to specify ranges. For example, “2016-2020” means “all years between 2016 to 2020”.");
  },
  formatValue_: function() {
      return this.getFieldValue('from')+'-'+this.getFieldValue('to');
  }
};

Blockly.Blocks['block_year_inc'] = {
  init: function() {
    this.appendDummyInput()
        .appendField("Start in")
        .appendField(new Blockly.FieldNumber(0, CRON_FIELD_DATA['Year'].range[0], CRON_FIELD_DATA['Year'].range[1]), "start");
    this.appendDummyInput()
        .appendField("every")
        .appendField(new Blockly.FieldNumber(0, CRON_FIELD_DATA['Year'].inc[0], CRON_FIELD_DATA['Year'].inc[1]), "inc")
        .appendField("year");
    this.setInputsInline(true);
    this.setOutput(true, 'block_year_inc');
    this.setColour(100);
    this.setTooltip("Used to specify increments. For example, “2016/2” means “every 2 years from 2016”.");
  },
  formatValue_: function() {
      return this.getFieldValue('start')+'/'+this.getFieldValue('inc');
  }
};
