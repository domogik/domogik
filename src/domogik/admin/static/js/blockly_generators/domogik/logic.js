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
 * @fileoverview Generating Domogik for logic blocks.
 * @author q.neutron@gmail.com (Quynh Neutron)
 */
'use strict';

goog.provide('Blockly.Domogik.logic');

goog.require('Blockly.Domogik');


Blockly.Domogik['controls_if'] = function(block) {
  // If/elseif/else condition.
  var n = 0;
  var argument = Blockly.Domogik.valueToCode(block, 'IF' + n,
      Blockly.Domogik.ORDER_NONE) || 'False';
  var branch = Blockly.Domogik.statementToCode(block, 'DO' + n) || 'null';
    var code = '{ "id":' + block.id 
    + ', "type":' + "controls_if"
    + ', "if0": ' + argument + ', "do0": ' + branch;

  for (n = 1; n <= block.elseifCount_; n++) {
    argument = Blockly.Domogik.valueToCode(block, 'IF' + n,
        Blockly.Domogik.ORDER_NONE) || 'False';
    branch = Blockly.Domogik.statementToCode(block, 'DO' + n) || 'null';
    code += ', "if' + n + '": ' + argument + ', "do' + n + '": ' + branch;
  }
  if (block.elseCount_) {
    branch = Blockly.Domogik.statementToCode(block, 'ELSE') || 'null';
    code += ', "else": ' + branch;
  }
  code += ' }';
  return code;
};

Blockly.Domogik['logic_compare'] = function(block) {
  var operator = block.getFieldValue('OP');
  var order = Blockly.Domogik.ORDER_RELATIONAL;
  var argument0 = Blockly.Domogik.valueToCode(block, 'A', order) || '0';
  var argument1 = Blockly.Domogik.valueToCode(block, 'B', order) || '0';
  var code = '{ "id":' + block.id 
    + ', "type":' + "logic_compare"
    + ', "op":' + operator
    + ', "a":' + argument0
    + ', "b":' + argument1 + ' }';
  return [code, order];
};

Blockly.Domogik['logic_operation'] = function(block) {
  // Operations 'and', 'or'.
  var operator = (block.getFieldValue('OP') == 'AND') ? 'AND' : 'OR';
  var order = (operator == 'AND') ? Blockly.Domogik.ORDER_LOGICAL_AND :
      Blockly.Domogik.ORDER_LOGICAL_OR;
  var argument0 = Blockly.Domogik.valueToCode(block, 'A', order);
  var argument1 = Blockly.Domogik.valueToCode(block, 'B', order);
  if (!argument0 && !argument1) {
    // If there are no arguments, then the return value is false.
    argument0 = 'False';
    argument1 = 'False';
  } else {
    // Single missing arguments have no effect on the return value.
    var defaultArgument = (operator == 'AND') ? 'True' : 'False';
    if (!argument0) {
      argument0 = defaultArgument;
    }
    if (!argument1) {
      argument1 = defaultArgument;
    }
  }
  var code = '{ "id":' + block.id 
    + ', "type":' + "logic_operation"
    + ', "op":' + operator
    + ', "a":' + argument0
    + ', "b":' + argument1 + ' }';
  return [code, order];
};

Blockly.Domogik['logic_negate'] = function(block) {
  // Negation.
  var argument0 = Blockly.Domogik.valueToCode(block, 'BOOL',
      Blockly.Domogik.ORDER_LOGICAL_NOT) || 'True';
  var code = '{ "id":' + block.id 
    + ', "type":' + "logic_negate" 
    + ', "bool": ' +  argument0 + ' }';
  return [code, Blockly.Domogik.ORDER_LOGICAL_NOT];
};

Blockly.Domogik['logic_boolean'] = function(block) {
  // Boolean values true and false.
  var value = (block.getFieldValue('BOOL') == 'TRUE') ? 'True' : 'False';
  var code = '{ "id":' + block.id 
    + ', "type":' + "logic_boolean" 
    + ', "bool": ' +  value + ' }';
  return [code, Blockly.Domogik.ORDER_ATOMIC];
};

Blockly.Domogik['logic_null'] = function(block) {
  // Null data type.
  var code = '{ "id":' + block.id 
    + ', "type":' + "logic_null" + ' }';
  return [code, Blockly.Domogik.ORDER_ATOMIC];
};

Blockly.Domogik['logic_ternary'] = function(block) {
  // Ternary operator.
  var value_if = Blockly.Domogik.valueToCode(block, 'IF',
      Blockly.Domogik.ORDER_CONDITIONAL) || 'False';
  var value_then = Blockly.Domogik.valueToCode(block, 'THEN',
      Blockly.Domogik.ORDER_CONDITIONAL) || 'None';
  var value_else = Blockly.Domogik.valueToCode(block, 'ELSE',
      Blockly.Domogik.ORDER_CONDITIONAL) || 'None';
  var code = '{ "id":' + block.id 
    + ', "type":' + "logic_ternary"
    + ', "if": ' + value_if
    + ', "then": ' + value_then
    + ', "else": ' + value_else
    + ' }';
  return [code, Blockly.Domogik.ORDER_CONDITIONAL];
};
