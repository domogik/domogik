/**
 * Visual Blocks Language
 *
 * Copyright 2012 Google Inc.
 * http://blockly.googlecode.com/
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *   http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

/**
 * @fileoverview Generating Domogik for text blocks.
 * @author q.neutron@gmail.com (Quynh Neutron)
 */
'use strict';

goog.provide('Blockly.Domogik.text');

goog.require('Blockly.Domogik');


Blockly.Domogik['text'] = function(block) {
  // Text value.
  var code = Blockly.Domogik.quote_(block.getFieldValue('TEXT'));
  return [code, Blockly.Domogik.ORDER_ATOMIC];
};

Blockly.Domogik['text_join'] = function(block) {
  // Create a string made up of any number of elements of any type.
  //Should we allow joining by '-' or ',' or any other characters?
  var code;
  if (block.itemCount_ == 0) {
    return ['\'\'', Blockly.Domogik.ORDER_ATOMIC];
  } else if (block.itemCount_ == 1) {
    var argument0 = Blockly.Domogik.valueToCode(block, 'ADD0',
        Blockly.Domogik.ORDER_NONE) || '\'\'';
    code = 'str(' + argument0 + ')';
    return [code, Blockly.Domogik.ORDER_FUNCTION_CALL];
  } else if (block.itemCount_ == 2) {
    var argument0 = Blockly.Domogik.valueToCode(block, 'ADD0',
        Blockly.Domogik.ORDER_NONE) || '\'\'';
    var argument1 = Blockly.Domogik.valueToCode(block, 'ADD1',
        Blockly.Domogik.ORDER_NONE) || '\'\'';
    var code = 'str(' + argument0 + ') + str(' + argument1 + ')';
    return [code, Blockly.Domogik.ORDER_UNARY_SIGN];
  } else {
    var code = [];
    for (var n = 0; n < block.itemCount_; n++) {
      code[n] = Blockly.Domogik.valueToCode(block, 'ADD' + n,
          Blockly.Domogik.ORDER_NONE) || '\'\'';
    }
    var tempVar = Blockly.Domogik.variableDB_.getDistinctName('temp_value',
        Blockly.Variables.NAME_TYPE);
    code = '\'\'.join([str(' + tempVar + ') for ' + tempVar + ' in [' +
        code.join(', ') + ']])';
    return [code, Blockly.Domogik.ORDER_FUNCTION_CALL];
  }
};

Blockly.Domogik['text_append'] = function(block) {
  // Append to a variable in place.
  var varName = Blockly.Domogik.variableDB_.getName(block.getFieldValue('VAR'),
      Blockly.Variables.NAME_TYPE);
  var argument0 = Blockly.Domogik.valueToCode(block, 'TEXT',
      Blockly.Domogik.ORDER_NONE) || '\'\'';
  return varName + ' = str(' + varName + ') + str(' + argument0 + ')\n';
};

Blockly.Domogik['text_length'] = function(block) {
  // String length.
  var argument0 = Blockly.Domogik.valueToCode(block, 'VALUE',
      Blockly.Domogik.ORDER_NONE) || '\'\'';
  return ['len(' + argument0 + ')', Blockly.Domogik.ORDER_FUNCTION_CALL];
};

Blockly.Domogik['text_isEmpty'] = function(block) {
  // Is the string null?
  var argument0 = Blockly.Domogik.valueToCode(block, 'VALUE',
      Blockly.Domogik.ORDER_NONE) || '\'\'';
  var code = 'not len(' + argument0 + ')';
  return [code, Blockly.Domogik.ORDER_LOGICAL_NOT];
};

Blockly.Domogik['text_indexOf'] = function(block) {
  // Search the text for a substring.
  // Should we allow for non-case sensitive???
  var operator = block.getFieldValue('END') == 'FIRST' ? 'find' : 'rfind';
  var argument0 = Blockly.Domogik.valueToCode(block, 'FIND',
      Blockly.Domogik.ORDER_NONE) || '\'\'';
  var argument1 = Blockly.Domogik.valueToCode(block, 'VALUE',
      Blockly.Domogik.ORDER_MEMBER) || '\'\'';
  var code = argument1 + '.' + operator + '(' + argument0 + ') + 1';
  return [code, Blockly.Domogik.ORDER_MEMBER];
};

Blockly.Domogik['text_charAt'] = function(block) {
  // Get letter at index.
  // Note: Until January 2013 this block did not have the WHERE input.
  var where = block.getFieldValue('WHERE') || 'FROM_START';
  var at = Blockly.Domogik.valueToCode(block, 'AT',
      Blockly.Domogik.ORDER_UNARY_SIGN) || '1';
  var text = Blockly.Domogik.valueToCode(block, 'VALUE',
      Blockly.Domogik.ORDER_MEMBER) || '\'\'';
  switch (where) {
    case 'FIRST':
      var code = text + '[0]';
      return [code, Blockly.Domogik.ORDER_MEMBER];
    case 'LAST':
      var code = text + '[-1]';
      return [code, Blockly.Domogik.ORDER_MEMBER];
    case 'FROM_START':
      // Blockly uses one-based indicies.
      if (Blockly.isNumber(at)) {
        // If the index is a naked number, decrement it right now.
        at = parseInt(at, 10) - 1;
      } else {
        // If the index is dynamic, decrement it in code.
        at = 'int(' + at + ' - 1)';
      }
      var code = text + '[' + at + ']';
      return [code, Blockly.Domogik.ORDER_MEMBER];
    case 'FROM_END':
      var code = text + '[-' + at + ']';
      return [code, Blockly.Domogik.ORDER_MEMBER];
    case 'RANDOM':
      Blockly.Domogik.definitions_['import_random'] = 'import random';
      var functionName = Blockly.Domogik.provideFunction_(
          'text_random_letter',
          ['def ' + Blockly.Domogik.FUNCTION_NAME_PLACEHOLDER_ + '(text):',
           '  x = int(random.random() * len(text))',
           '  return text[x];']);
      code = functionName + '(' + text + ')';
      return [code, Blockly.Domogik.ORDER_FUNCTION_CALL];
  }
  throw 'Unhandled option (text_charAt).';
};

Blockly.Domogik['text_getSubstring'] = function(block) {
  // Get substring.
  var text = Blockly.Domogik.valueToCode(block, 'STRING',
      Blockly.Domogik.ORDER_MEMBER) || '\'\'';
  var where1 = block.getFieldValue('WHERE1');
  var where2 = block.getFieldValue('WHERE2');
  var at1 = Blockly.Domogik.valueToCode(block, 'AT1',
      Blockly.Domogik.ORDER_ADDITIVE) || '1';
  var at2 = Blockly.Domogik.valueToCode(block, 'AT2',
      Blockly.Domogik.ORDER_ADDITIVE) || '1';
  if (where1 == 'FIRST' || (where1 == 'FROM_START' && at1 == '1')) {
    at1 = '';
  } else if (where1 == 'FROM_START') {
    // Blockly uses one-based indicies.
    if (Blockly.isNumber(at1)) {
      // If the index is a naked number, decrement it right now.
      at1 = parseInt(at1, 10) - 1;
    } else {
      // If the index is dynamic, decrement it in code.
      at1 = 'int(' + at1 + ' - 1)';
    }
  } else if (where1 == 'FROM_END') {
    if (Blockly.isNumber(at1)) {
      at1 = -parseInt(at1, 10);
    } else {
      at1 = '-int(' + at1 + ')';
    }
  }
  if (where2 == 'LAST' || (where2 == 'FROM_END' && at2 == '1')) {
    at2 = '';
  } else if (where1 == 'FROM_START') {
    if (Blockly.isNumber(at2)) {
      at2 = parseInt(at2, 10);
    } else {
      at2 = 'int(' + at2 + ')';
    }
  } else if (where1 == 'FROM_END') {
    if (Blockly.isNumber(at2)) {
      // If the index is a naked number, increment it right now.
      at2 = 1 - parseInt(at2, 10);
      if (at2 == 0) {
        at2 = '';
      }
    } else {
      // If the index is dynamic, increment it in code.
      // Add special case for -0.
      Blockly.Domogik.definitions_['import_sys'] = 'import sys';
      at2 = 'int(1 - ' + at2 + ') or sys.maxsize';
    }
  }
  var code = text + '[' + at1 + ' : ' + at2 + ']';
  return [code, Blockly.Domogik.ORDER_MEMBER];
};

Blockly.Domogik['text_changeCase'] = function(block) {
  // Change capitalization.
  var OPERATORS = {
    UPPERCASE: '.upper()',
    LOWERCASE: '.lower()',
    TITLECASE: '.title()'
  };
  var operator = OPERATORS[block.getFieldValue('CASE')];
  var argument0 = Blockly.Domogik.valueToCode(block, 'TEXT',
      Blockly.Domogik.ORDER_MEMBER) || '\'\'';
  var code = argument0 + operator;
  return [code, Blockly.Domogik.ORDER_MEMBER];
};

Blockly.Domogik['text_trim'] = function(block) {
  // Trim spaces.
  var OPERATORS = {
    LEFT: '.lstrip()',
    RIGHT: '.rstrip()',
    BOTH: '.strip()'
  };
  var operator = OPERATORS[block.getFieldValue('MODE')];
  var argument0 = Blockly.Domogik.valueToCode(block, 'TEXT',
      Blockly.Domogik.ORDER_MEMBER) || '\'\'';
  var code = argument0 + operator;
  return [code, Blockly.Domogik.ORDER_MEMBER];
};

Blockly.Domogik['text_print'] = function(block) {
  // Print statement.
  var argument0 = Blockly.Domogik.valueToCode(block, 'TEXT',
      Blockly.Domogik.ORDER_NONE) || '\'\'';
  return 'print(' + argument0 + ')\n';
};

Blockly.Domogik['text_prompt'] = function(block) {
  // Prompt function.
  var functionName = Blockly.Domogik.provideFunction_(
      'text_prompt',
      ['def ' + Blockly.Domogik.FUNCTION_NAME_PLACEHOLDER_ + '(msg):',
       '  try:',
       '    return raw_input(msg)',
       '  except NameError:',
       '    return input(msg)']);
  var msg = Blockly.Domogik.quote_(block.getFieldValue('TEXT'));
  var code = functionName + '(' + msg + ')';
  var toNumber = block.getFieldValue('TYPE') == 'NUMBER';
  if (toNumber) {
    code = 'float(' + code + ')';
  }
  return [code, Blockly.Domogik.ORDER_FUNCTION_CALL];
};
