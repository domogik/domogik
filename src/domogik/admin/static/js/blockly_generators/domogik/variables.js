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
 * @fileoverview Generating Domogik for variable blocks.
 * @author q.neutron@gmail.com (Quynh Neutron)
 */
'use strict';

goog.provide('Blockly.Domogik.variables');

goog.require('Blockly.Domogik');


Blockly.Domogik['variables_get'] = function(block) {
  // Variable getter.
  var code = Blockly.Domogik.variableDB_.getName(block.getFieldValue('VAR'),
      Blockly.Variables.NAME_TYPE);
  return [code, Blockly.Domogik.ORDER_ATOMIC];
};

Blockly.Domogik['variables_set'] = function(block) {
  // Variable setter.
  var argument0 = Blockly.Domogik.valueToCode(block, 'VALUE',
      Blockly.Domogik.ORDER_NONE) || '0';
  var varName = Blockly.Domogik.variableDB_.getName(block.getFieldValue('VAR'),
      Blockly.Variables.NAME_TYPE);
  return varName + ' = ' + argument0 + '\n';
};
