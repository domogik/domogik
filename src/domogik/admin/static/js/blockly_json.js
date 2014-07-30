/**
 * @license
 * Visual Blocks Editor
 *
 * Copyright 2012 Google Inc.
 * https://blockly.googlecode.com/
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
 * @fileoverview XML reader and writer.
 * @author fraser@google.com (Neil Fraser)
 */
'use strict';

goog.provide('Blockly.JSON');

/**
 * Decode an XML DOM and create blocks on the workspace.
 * @param {!Blockly.Workspace} workspace The SVG workspace.
 * @param {!Element} JSON.
 */
Blockly.JSON.jsonToWorkspace = function(workspace, json) {
  Blockly.JSON.jsonToBlock(workspace, json);
};

/**
 * Decode an XML block tag and create a block (and possibly sub blocks) on the
 * workspace.
 * @param {!Blockly.Workspace} workspace The workspace.
 * @param {!Element} JSON block element.
 * @param {boolean=} opt_reuseBlock Optional arg indicating whether to
 *     reinitialize an existing block.
 * @return {!Blockly.Block} The root block created.
 * @private
 */
Blockly.JSON.jsonToBlock = function(workspace, jsonBlock, opt_reuseBlock) {
  var block = null;
  var prototypeName = jsonBlock['type'];
  if (!prototypeName) {
    throw 'Block type unspecified: \n';
  }
  var id = jsonBlock['id'];
  if (opt_reuseBlock && id) {
    block = Blockly.Block.getById(id, workspace);
    // TODO: The following is for debugging.  It should never actually happen.
    if (!block) {
      throw 'Couldn\'t get Block with id: ' + id;
    }
    var parentBlock = block.getParent();
    // If we've already filled this block then we will dispose of it and then
    // re-fill it.
    if (block.workspace) {
      block.dispose(true, false, true);
    }
    block.fill(workspace, prototypeName);
    block.parent_ = parentBlock;
  } else {
    block = Blockly.Block.obtain(workspace, prototypeName);
//    if (id) {
//      block.id = parseInt(id, 10);
//    }
  }
  if (!block.svg_) {
    block.initSvg();
  }

  var inline = jsonBlock['inline'];
  if (inline) {
    block.setInputsInline(inline == 'true');
  }
  var disabled = jsonBlock['disabled'];
  if (disabled) {
    block.setDisabled(disabled == 'true');
  }
  var deletable = jsonBlock['deletable'];
  if (deletable) {
    block.setDeletable(deletable == 'true');
  }
  var movable = jsonBlock['movable'];
  if (movable) {
    block.setMovable(movable == 'true');
  }
  var editable = jsonBlock['editable'];
  if (editable) {
    block.setEditable(editable == 'true');
  }

  var blockChild = null;

  for(var keyx in jsonBlock) {
    if (['id', 'type'].indexOf(keyx) == -1 && typeof(jsonBlock[keyx]) === 'object' ) {
      var jsonChild = jsonBlock[keyx];
      console.debug(keyx, typeof(jsonBlock[keyx]));
      var input;

      // Find the first 'real' grandchild node (that isn't whitespace).
      var firstRealGrandchild = null;
      for(var keyy in jsonChild) {
        if (['id', 'type'].indexOf(keyy) == -1 && typeof(jsonChild[keyy]) === 'object' ) {
          firstRealGrandchild = jsonChild[keyy];
        }
      }
      /*
      var name = jsonChild['name'];
      
      switch (jsonNameChild.nodeName.toLowerCase()) {
        case 'mutation':
          // Custom data for an advanced block.
          if (block.domToMutation) {
            block.domToMutation(xmlChild);
          }
          break;
        case 'comment':
          block.setCommentText(xmlChild.textContent);
          var visible = xmlChild.getAttribute('pinned');
          if (visible) {
            // Give the renderer a millisecond to render and position the block
            // before positioning the comment bubble.
            setTimeout(function() {
              block.comment.setVisible(visible == 'true');
            }, 1);
          }
          var bubbleW = parseInt(xmlChild.getAttribute('w'), 10);
          var bubbleH = parseInt(xmlChild.getAttribute('h'), 10);
          if (!isNaN(bubbleW) && !isNaN(bubbleH)) {
            block.comment.setBubbleSize(bubbleW, bubbleH);
          }
          break;
        case 'field':
          block.setFieldValue(xmlChild.textContent, name);
          break;
        case 'value':
        case 'statement':
          input = block.getInput(name);
          if (!input) {
            throw 'Input ' + name + ' does not exist in block ' + prototypeName;
          }
          if (firstRealGrandchild &&
              firstRealGrandchild.nodeName.toLowerCase() == 'block') {
            blockChild = Blockly.JSON.domToBlock(workspace, firstRealGrandchild,
                opt_reuseBlock);
            if (blockChild.outputConnection) {
              input.connection.connect(blockChild.outputConnection);
            } else if (blockChild.previousConnection) {
              input.connection.connect(blockChild.previousConnection);
            } else {
              throw 'Child block does not have output or previous statement.';
            }
          }
          break;
        case 'next':
          if (firstRealGrandchild &&
              firstRealGrandchild.nodeName.toLowerCase() == 'block') {
            if (!block.nextConnection) {
              throw 'Next statement does not exist.';
            } else if (block.nextConnection.targetConnection) {
              // This could happen if there is more than one XML 'next' tag.
              throw 'Next statement is already connected.';
            }
            blockChild = Blockly.JSON.domToBlock(workspace, firstRealGrandchild,
                opt_reuseBlock);
            if (!blockChild.previousConnection) {
              throw 'Next block does not have previous statement.';
            }
            block.nextConnection.connect(blockChild.previousConnection);
          }
          break;
        default:
          // Unknown tag; ignore.  Same principle as HTML parsers.
      }*/
    }
  }

  var collapsed = jsonBlock['collapsed'];
  if (collapsed) {
    block.setCollapsed(collapsed == 'true');
  }
  var next = block.getNextBlock();
  if (next) {
    // Next block in a stack needs to square off its corners.
    // Rendering a child will render its parent.
    next.render();
  } else {
    block.render();
  }
  return block;
};

// Export symbols that would otherwise be renamed by Closure compiler.
Blockly['JSON'] = Blockly.JSON;
Blockly.JSON['jsonToWorkspace'] = Blockly.JSON.jsonToWorkspace;
