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
        "help" : "",
        "check": ['block_all','block_minute_at','block_minute_from_to','block_minute_inc'],
        "rule" : CRON_GENERAL
    },
    "Hour": {
        "label": "Hour",
        "help" : "",
        "check": ['block_all','block_hour_at','block_hour_from_to','block_hour_inc'],
        "rule" : CRON_GENERAL
    },
    "DayOfMonth": {
        "label": "Day of month",
        "help" : "",
        "check": ['block_all','block_last','block_no_specif','block_day_of_month_at','block_day_of_month_from_to','block_day_of_month_inc','block_day_of_month_w','block_day_of_month_from_to'],
        "rule" : CRON_D_MONTH
    },
    "Month":  {
        "label": "Month",
        "help" : "",
        "check": ['block_all','block_month_on','block_month_from_to','block_month_inc'],
        "rule" : CRON_GENERAL
    },
    "DayOfWeek":  {
        "label": "Day of week",
        "help" : "",
        "check": ['block_all','block_last','block_no_specif','block_day_w_on','block_day_w_from_to','block_day_w_inc','block_day_w_last_of_month','block_day_w_nth_of_month','block_day_w_w_end'],
        "rule" : CRON_D_WEEK
    },
    "Year":  {
        "label": "Year (optional)",
        "help" : "",
        "check": ['block_all','block_year_in','block_year_from_to','block_year_inc'],
        "rule" : CRON_GENERAL
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
var WEEKDAYS = [["Sunday", "0"], ["Monday", "1"], ["Thuesday", "2"], ["Wednesday", "3"], ["Wednesday", "4"], ["Friday", "5"], ["Saturday", "6"]];
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
    this.setHelpUrl('');
    this.initDialCheck = false;
    this.validCron = false;
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
                    .appendField(CRON_FIELD_DATA[input].label)
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
    if (exp in EPHEM_TRANLATION) {
        trad = EPHEM_TRANLATION[exp];
    } else if (exp in PREDEFINED_TRANLATION) {
        trad = PREDEFINED_TRANLATION[exp];
    } else {
        var trad = "Can't translate cron expression."
        var item = exp.split(' ');
        if (item.length == 5 || item.length == 6) {
            if (exp && exp.indexOf("Bad cron format") == -1) {
                try {
                    // Add second if year is set
                    if (item.length == 6) {item.unshift("0");};
                    trad = cronstrue.toString(exp, { locale: navigator.language });
                } catch (err) {};
            };
        };
    };
    this.setTooltip(trad);
    if (this.tooltip.indexOf("Can't translate") != -1 || trad == "") {
        this.validCron = false;
        this.getField('btCheck').setValue('/static/images/icon-cron-invalid.png');
    } else {
        this.validCron = true;
        this.getField('btCheck').setValue('/static/images/icon-cron-valid.png');
    };
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
                            return 'Bad cron format ! ('+exp+')';
                        };
                    };
                    exp = exp.replace(/,$/, " ");
                } else {
                    exp += inputBlock.formatValue_() + ' ';
                };
            } else {
                return 'Bad cron format ! ('+exp+')';
            };
        } else {
            if (inputBlock) {
                if (inputBlock.type == 'lists_create_with') {
                    for (var x = 0, input; input = inputBlock.inputList[x]; x++) {
                        var item = input.connection.targetBlock();
                        if (item) {
                            exp += item.formatValue_() + ',';
                        } else {
                            return 'Bad cron format ! ('+exp+')';
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
        this.generateCronInput_(item[0], 'Minute', this.MinuteToBlock_);
        this.generateCronInput_(item[1], 'Hour', this.HourToBlock_);
        this.generateCronInput_(item[2], 'DayOfMonth', this.DayOfMonthToBlock_);
        this.generateCronInput_(item[3], 'Month', this.MonthToBlock_);
        this.generateCronInput_(item[4], 'DayOfWeek', this.DayOfWeekToBlock_);
        if (item.length == 6) {
            this.generateCronInput_(item[5], 'Year', this.YearToBlock_);
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
        var nBlock = null;
        if (exp.crontype.specChar == '*'){
          var nBlock = this.workspace.newBlock('block_all');
        } else if (exp.crontype.specChar == '-') {
            var nBlock = this.workspace.newBlock('block_minute_from_to');
            nBlock.setFieldValue(exp.values[0], 'from');
            nBlock.setFieldValue(exp.values[1], 'to');
        } else if (exp.crontype.specChar == '/') {
            var nBlock = this.workspace.newBlock('block_minute_inc');
            nBlock.setFieldValue(exp.values[0], 'start');
            nBlock.setFieldValue(exp.values[1], 'inc');
        } else if (exp.crontype.specChar == '') {
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
        var nBlock = null;
        if (exp.crontype.specChar == '*'){
          var nBlock = this.workspace.newBlock('block_all');
        } else if (exp.crontype.specChar == '-') {
            var nBlock = this.workspace.newBlock('block_hour_from_to');
            nBlock.setFieldValue(exp.values[0], 'from');
            nBlock.setFieldValue(exp.values[1], 'to');
        } else if (exp.crontype.specChar == '/') {
            var nBlock = this.workspace.newBlock('block_hour_inc');
            nBlock.setFieldValue(exp.values[0], 'start');
            nBlock.setFieldValue(exp.values[1], 'inc');
        } else if (exp.crontype.specChar == '') {
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
        var nBlock = null;
        if (exp.crontype.specChar == '*'){
          var nBlock = this.workspace.newBlock('block_all');
        } else if (exp.crontype.specChar == '-') {
            var nBlock = this.workspace.newBlock('block_day_of_month_from_to');
            nBlock.setFieldValue(exp.values[0], 'from');
            nBlock.setFieldValue(exp.values[1], 'to');
        } else if (exp.crontype.specChar == '/') {
            var nBlock = this.workspace.newBlock('block_day_of_month_inc');
            nBlock.setFieldValue(exp.values[0], 'start');
            nBlock.setFieldValue(exp.values[1], 'inc');
        } else if (exp.crontype.specChar == 'L') {
            var nBlock = this.workspace.newBlock('block_last');
        } else if (exp.crontype.specChar == 'W') {
            if (exp.values.length == 0) {
                var nBlock = this.workspace.newBlock('block_day_of_month_w');
            } else {
                var nBlock = this.workspace.newBlock('block_day_of_month_near_to_w');
                nBlock.setFieldValue(exp.values[0], 'day_m');
            };
        } else if (exp.crontype.specChar == '?') {
            var nBlock = this.workspace.newBlock('block_no_specif');
        } else if (exp.crontype.specChar == '') {
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
        var nBlock = null;
        if (exp.crontype.specChar == '*'){
          var nBlock = this.workspace.newBlock('block_all');
        } else if (exp.crontype.specChar == '-') {
            var nBlock = this.workspace.newBlock('block_month_from_to');
            nBlock.setFieldValue(exp.values[0], 'from');
            nBlock.setFieldValue(exp.values[1], 'to');
        } else if (exp.crontype.specChar == '/') {
            var nBlock = this.workspace.newBlock('block_month_inc');
            nBlock.setFieldValue(exp.values[0], 'start');
            nBlock.setFieldValue(exp.values[1], 'inc');
        } else if (exp.crontype.specChar == '') {
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
        var nBlock = null;
        if (exp.crontype.specChar == '*'){
          var nBlock = this.workspace.newBlock('block_all');
        } else if (exp.crontype.specChar == '-') {
            var nBlock = this.workspace.newBlock('block_day_w_from_to');
            nBlock.setFieldValue(exp.values[0], 'from');
            nBlock.setFieldValue(exp.values[1], 'to');
        } else if (exp.crontype.specChar == '/') {
            var nBlock = this.workspace.newBlock('block_day_w_inc');
            nBlock.setFieldValue(exp.values[0], 'start');
            nBlock.setFieldValue(exp.values[1], 'inc');
        } else if (exp.crontype.specChar == '?') {
            var nBlock = this.workspace.newBlock('block_no_specif');
        } else if (exp.crontype.specChar == 'L') {
            if (exp.values.length == 0) {
                var nBlock = this.workspace.newBlock('block_last');
            } else {
                var nBlock = this.workspace.newBlock('block_day_w_last_of_month');
                nBlock.setFieldValue(exp.values[0], 'day_w');
            };
        } else if (exp.crontype.specChar == '#') {
            var nBlock = this.workspace.newBlock('block_day_w_nth_of_month');
            nBlock.setFieldValue(exp.values[0], 'day_w');
            nBlock.setFieldValue(exp.values[1], 'nth');
        } else if (exp.crontype.specChar == '') {
            var nBlock = this.workspace.newBlock('block_day_w_on');
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
        var nBlock = null;
        if (exp.crontype.specChar == '*'){
          var nBlock = this.workspace.newBlock('block_all');
        } else if (exp.crontype.specChar == '-') {
            var nBlock = this.workspace.newBlock('block_year_from_to');
            nBlock.setFieldValue(exp.values[0], 'from');
            nBlock.setFieldValue(exp.values[1], 'to');
        } else if (exp.crontype.specChar == '/') {
            var nBlock = this.workspace.newBlock('block_year_inc');
            nBlock.setFieldValue(exp.values[0], 'start');
            nBlock.setFieldValue(exp.values[1], 'inc');
        } else if (exp.crontype.specChar == '') {
            var nBlock = this.workspace.newBlock('block_year_in');
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
    this.setHelpUrl('');
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
    this.setTooltip('');
    this.setHelpUrl('');
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
    this.setTooltip('');
    this.setHelpUrl('');
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
    this.setHelpUrl('');
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
        .appendField(new Blockly.FieldNumber(0, 0, 59), "minute")
        .appendField("mn");
    this.setOutput(true, 'block_minute_at');
    this.setColour(160);
    this.setTooltip('');
    this.setHelpUrl('');
  },
  formatValue_: function() {
      return this.getFieldValue('minute');
  }
};

Blockly.Blocks['block_minute_from_to'] = {
  init: function() {
    this.appendDummyInput()
        .appendField("From")
        .appendField(new Blockly.FieldNumber(0, 0, 59), "from")
        .appendField("mn");
    this.appendDummyInput()
        .appendField("to")
        .appendField(new Blockly.FieldNumber(0, 0, 59), "to")
        .appendField("mn");
    this.setInputsInline(true);
    this.setOutput(true, 'block_minute_from_to');
    this.setColour(160);
    this.setTooltip('Used to specify ranges. For example, “5-10” in the minute field means “all minutes between 5 to 10”.');
    this.setHelpUrl('');
  },
  formatValue_: function() {
      return this.getFieldValue('from')+'-'+this.getFieldValue('to');
  }
};

Blockly.Blocks['block_minute_inc'] = {
  init: function() {
    this.appendDummyInput()
        .appendField("Starting from")
        .appendField(new Blockly.FieldNumber(0, 0, 59), "start")
        .appendField("mn");
    this.appendDummyInput()
        .appendField("every")
        .appendField(new Blockly.FieldNumber(0, 0, 59), "inc")
        .appendField("mn");
    this.setInputsInline(true);
    this.setOutput(true, 'block_minute_inc');
    this.setColour(160);
    this.setTooltip('');
    this.setHelpUrl('');
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
        .appendField(new Blockly.FieldNumber(0, 0, 23), "hour")
        .appendField("h");
    this.setOutput(true, 'block_hour_at');
    this.setColour(230);
    this.setTooltip('');
    this.setHelpUrl('');
  },
  formatValue_: function() {
      return this.getFieldValue('hour');
  }
};

Blockly.Blocks['block_hour_from_to'] = {
  init: function() {
    this.appendDummyInput()
        .appendField("From")
        .appendField(new Blockly.FieldNumber(0, 0, 23), "from")
        .appendField("h");
    this.appendDummyInput()
        .appendField("to")
        .appendField(new Blockly.FieldNumber(0, 0, 23), "to")
        .appendField("h");
    this.setInputsInline(true);
    this.setOutput(true, 'block_hour_from_to');
    this.setColour(230);
    this.setTooltip('');
    this.setHelpUrl('');
  },
  formatValue_: function() {
      return this.getFieldValue('from')+'-'+this.getFieldValue('to');
  }
};

Blockly.Blocks['block_hour_inc'] = {
  init: function() {
    this.appendDummyInput()
        .appendField("Starting from")
        .appendField(new Blockly.FieldNumber(0, 0, 23), "start")
        .appendField("h");
    this.appendDummyInput()
        .appendField("every")
        .appendField(new Blockly.FieldNumber(0, 0, 23), "inc")
        .appendField("h");
    this.setInputsInline(true);
    this.setOutput(true, 'block_hour_inc');
    this.setColour(230);
    this.setTooltip('');
    this.setHelpUrl('');
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
        .appendField(new Blockly.FieldNumber(1, 1, 31), "day_m")
        .appendField("of month");
    this.setOutput(true, 'block_day_of_month_at');
    this.setColour(65);
    this.setTooltip('');
    this.setHelpUrl('');
  },
  formatValue_: function() {
      return this.getFieldValue('day_m');
  }
};

Blockly.Blocks['block_day_of_month_from_to'] = {
  init: function() {
    this.appendDummyInput()
        .appendField("From")
        .appendField(new Blockly.FieldNumber(1, 1, 31), "from");
    this.appendDummyInput()
        .appendField("to")
        .appendField(new Blockly.FieldNumber(1, 1, 31), "to")
        .appendField("of the month");
    this.setInputsInline(true);
    this.setOutput(true, 'block_day_of_month_from_to');
    this.setColour(65);
    this.setTooltip('');
    this.setHelpUrl('');
  },
  formatValue_: function() {
      return this.getFieldValue('from')+'-'+this.getFieldValue('to');
  }
};

Blockly.Blocks['block_day_of_month_inc'] = {
  init: function() {
    this.appendDummyInput()
        .appendField("Starting from")
        .appendField(new Blockly.FieldNumber(1, 1, 31), "start");
    this.appendDummyInput()
        .appendField("of the month every")
        .appendField(new Blockly.FieldNumber(1, 1, 31), "inc")
        .appendField("day");
    this.setInputsInline(true);
    this.setOutput(true, 'block_day_of_month_inc');
    this.setColour(65);
    this.setTooltip('');
    this.setHelpUrl('');
  },
  formatValue_: function() {
      return this.getFieldValue('start')+'/'+this.getFieldValue('inc');
  }
};

Blockly.Blocks['block_day_of_month_w'] = {
  init: function() {
    this.appendDummyInput()
        .appendField("On weekdays");
    this.setInputsInline(true);
    this.setOutput(true, 'block_day_of_month_w');
    this.setColour(65);
    this.setTooltip('');
    this.setHelpUrl('');
  },
  formatValue_: function() {
      return 'W';
  }
};

Blockly.Blocks['block_day_of_month_near_to_w'] = {
  init: function() {
    this.appendDummyInput()
        .appendField("The nearest weekday to the")
        .appendField(new Blockly.FieldNumber(1, 1, 31), "day_m")
        .appendField("of the month");
    this.setInputsInline(true);
    this.setOutput(true, 'block_day_of_month_near_to_w');
    this.setColour(65);
    this.setTooltip('');
    this.setHelpUrl('');
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
    this.setTooltip('');
    this.setHelpUrl('');
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
    this.setTooltip('');
    this.setHelpUrl('');
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
        .appendField(new Blockly.FieldNumber(1, 1, 11), "inc")
        .appendField("month");
    this.setInputsInline(true);
    this.setOutput(true, 'block_month_inc');
    this.setColour(45);
    this.setTooltip('');
    this.setHelpUrl('');
  },
  formatValue_: function() {
      return this.getFieldValue('start')+'/'+this.getFieldValue('inc');
  }
};

// Block month
Blockly.Blocks['block_day_w_on'] = {
  init: function() {
    this.appendDummyInput()
        .appendField("On")
        .appendField(new Blockly.FieldDropdown(WEEKDAYS), "day_w");
    this.setInputsInline(true);
    this.setOutput(true, 'block_day_w_on');
    this.setColour(290);
    this.setTooltip('');
    this.setHelpUrl('');
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
    this.setTooltip('');
    this.setHelpUrl('');
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
        .appendField(new Blockly.FieldNumber(1, 1, 6), "inc")
        .appendField("day");
    this.setInputsInline(true);
    this.setOutput(true, 'block_day_w_inc');
    this.setColour(290);
    this.setTooltip('');
    this.setHelpUrl('');
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
    this.setTooltip('');
    this.setHelpUrl('');
  },
  formatValue_: function() {
      return this.getFieldValue('day_w')+'L';
  }
};

Blockly.Blocks['block_day_w_nth_of_month'] = {
  init: function() {
    this.appendDummyInput()
        .appendField("The")
        .appendField(new Blockly.FieldDropdown([["1st", "1"], ["2nd", "2"], ["3rd", "3"], ["4th", "4"], ["5th", "5"], ["6th", "6"]]), "nth")
    this.appendDummyInput()
        .appendField(new Blockly.FieldDropdown(WEEKDAYS), "day_w")
        .appendField("of the month");
    this.setInputsInline(true);
    this.setOutput(true, 'block_day_w_nth_of_month');
    this.setColour(290);
    this.setTooltip('');
    this.setHelpUrl('');
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
    this.setTooltip('');
    this.setHelpUrl('');
  },
  formatValue_: function() {
      return 'SAT,SUN';
  }
};

// Block year
Blockly.Blocks['block_year_in'] = {
  init: function() {
    this.appendDummyInput()
        .appendField("In")
        .appendField(new Blockly.FieldNumber(0, 0, 9999), "year");
    this.setOutput(true, 'block_year_in');
    this.setColour(100);
    this.setTooltip('');
    this.setHelpUrl('');
  },
  formatValue_: function() {
      return this.getFieldValue('year');
  }
};

Blockly.Blocks['block_year_from_to'] = {
  init: function() {
    this.appendDummyInput()
        .appendField("From")
        .appendField(new Blockly.FieldNumber(0, 0, 9999), "from");
    this.appendDummyInput()
        .appendField("to")
        .appendField(new Blockly.FieldNumber(0, 0, 9999), "to");
    this.setInputsInline(true);
    this.setOutput(true, 'block_year_from_to');
    this.setColour(100);
    this.setTooltip('');
    this.setHelpUrl('');
  },
  formatValue_: function() {
      return this.getFieldValue('from')+'-'+this.getFieldValue('to');
  }
};

Blockly.Blocks['block_year_inc'] = {
  init: function() {
    this.appendDummyInput()
        .appendField("Start in")
        .appendField(new Blockly.FieldNumber(0, 1, 9999), "start");
    this.appendDummyInput()
        .appendField("every")
        .appendField(new Blockly.FieldNumber(0, 0, 9999), "inc")
        .appendField("year");
    this.setInputsInline(true);
    this.setOutput(true, 'block_year_inc');
    this.setColour(100);
    this.setTooltip('');
    this.setHelpUrl('');
  },
  formatValue_: function() {
      return this.getFieldValue('start')+'/'+this.getFieldValue('inc');
  }
};
