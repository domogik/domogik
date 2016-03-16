'use strict';
goog.provide('Blockly.JSON');
Blockly.JSON.workspaceToJson = function(workspace) {
  var blocks = workspace.getTopBlocks(true);
  if (blocks[0]) {
    var json = Blockly.JSON.blockToJson(blocks[0]);
  }
  return JSON.stringify(json);
};
Blockly.JSON.blockToJson = function(block) {
  var element = {};
  element['type'] = block.type;
  element['id'] = block.id;
  for (var x = 0, input; input = block.inputList[x]; x++) {
    for (var y = 0, field; field = input.fieldRow[y]; y++) {
      if (field.name && field.EDITABLE) {
        element[field.name] = field.getValue();
      }
    }
  }
  var hasValues = false;
  for (var i = 0, input; input = block.inputList[i]; i++) {
    var empty = true;
    if (input.type == Blockly.DUMMY_INPUT) {
      continue;
    } else {
      var childBlock = input.connection.targetBlock();
      if (childBlock) {
        element[input.name] = Blockly.JSON.blockToJson(childBlock);
      }
    }
  }
  if (hasValues) { element['inline'] = block.inputsInline; }
  if (block.isCollapsed()) { element['collapsed'] = true; }
  if (block.disabled) { element['disabled'] = true; }
  if (!block.isDeletable()) { element['deletable'] = false; }
  if (!block.isMovable()) { element['movable'] = false; }
  if (!block.isEditable()) { element['editable'] = false; }
  if ( block.elseifCount_ ) { element['elseifCount'] = block.elseifCount_ }
  if ( block.elseCount_ ) { element['elseCount'] = block.elseCount_ }
  if ( block.itemCount_ ) { element['itemCount'] = block.itemCount_ }
  var nextBlock = block.getNextBlock();
  if (nextBlock) {
    element['NEXT']= Blockly.JSON.blockToJson(nextBlock);
  }
  return element;
};
Blockly.JSON.jsonToWorkspace = function(workspace, json) {
  Blockly.Events.disable();
  var topBlock = Blockly.JSON.jsonToBlock(workspace, json);
  if (workspace.rendered) {
    topBlock.setConnectionsHidden(true);
    var blocks = topBlock.getDescendants();
    for (var i = blocks.length - 1; i >= 0; i--) {
      blocks[i].initSvg();
    }
    for (var i = blocks.length - 1; i >= 0; i--) {
      blocks[i].render(false);
    }
    setTimeout(function() {
      if (topBlock.workspace) {  // Check that the block hasn't been deleted.
        topBlock.setConnectionsHidden(false);
      }
    }, 1);
    topBlock.updateDisabled();
    Blockly.fireUiEvent(window, 'resize');
  }
  Blockly.Events.enable();
  if (Blockly.Events.isEnabled() && !topBlock.isShadow()) {
    Blockly.Events.fire(new Blockly.Events.Create(topBlock));
  }
  return topBlock;
};
Blockly.JSON.jsonToBlock = function(workspace, jsonBlock) {
  var block = null;
  var prototypeName = jsonBlock['type'];
  var id = jsonBlock['id'];
  if (!prototypeName) { throw 'Block type unspecified: \n'; }
  if (!id) { throw 'Block id unspecified: \n'; }
  block = workspace.newBlock( prototypeName);
  block.id = jsonBlock['id'];
  if (!block.svg_) { block.initSvg(); }
  var inline = jsonBlock['inline'];
  if (inline) { block.setInputsInline(inline == 'true'); }
  var disabled = jsonBlock['disabled'];
  if (disabled) { block.setDisabled(disabled == 'true'); }
  var deletable = jsonBlock['deletable'];
  if (deletable) { block.setDeletable(deletable == 'true'); }
  var movable = jsonBlock['movable'];
  if (movable) { block.setMovable(movable == 'true'); }
  var editable = jsonBlock['editable'];
  if (editable) { block.setEditable(editable == 'true'); }
  var collapsed = jsonBlock['collapsed'];
  if (collapsed) { block.setCollapsed(collapsed == 'true'); }
  // handle mutations
  if ( block.domToMutation) {
      var mut = document.createElement('div');
      if ( jsonBlock['elseifCount'] ) {
        mut.setAttribute('elseif', jsonBlock['elseifCount'])
      }
      if ( jsonBlock['elseCount'] ) {
        mut.setAttribute('else', jsonBlock['elseCount'])
      }
      if ( jsonBlock['itemCount'] ) {
        mut.setAttribute('items', jsonBlock['itemCount'])
      }
      block.domToMutation(mut);
  }

  var blockChild = null;
  for(var key in jsonBlock) {
    if (['id', 'type'].indexOf(key) == -1) {
      var jsonChild = jsonBlock[key];
      if (jsonChild) { // not null
        var input;
        switch (typeof(jsonChild)) {
          case 'string':
          case 'boolean':
            block.setFieldValue(jsonChild, key);
            break;
          case 'object':
            blockChild = Blockly.JSON.jsonToBlock(workspace, jsonChild);
            if (key == 'NEXT') {
              if (!block.nextConnection) {
                throw 'Next statement does not exist.';
              } else if (block.nextConnection.targetConnection) {
                throw 'Next statement is already connected.';
              }
              if (!blockChild.previousConnection) {
                throw 'Next block does not have previous statement.';
              }
              block.nextConnection.connect(blockChild.previousConnection);
            } else {
              input = block.getInput(key);
              if (!input) {
                throw 'Input ' + key + ' does not exist in block ' + prototypeName;
              }
              if (blockChild.outputConnection) {
                input.connection.connect(blockChild.outputConnection);
              } else if (blockChild.previousConnection) {
                input.connection.connect(blockChild.previousConnection);
              } else {
                throw 'Child block does not have output or previous statement.';
              }
            }
            break;
          default:
            // Unknown tag; ignore.  Same principle as HTML parsers.
        }
      }
    }
  }
  if(block.afterRender) { block.afterRender(); }
  if (block.validate) { block.validate(); }
  var next = block.nextConnection && block.nextConnection.targetBlock();
  if (next) {
    next.render();
  } else {
    block.render();
  }
  return block;
};

// Export symbols that would otherwise be renamed by Closure compiler.
Blockly['JSON'] = Blockly.JSON;
Blockly.JSON['jsonToWorkspace'] = Blockly.JSON.jsonToWorkspace;
Blockly.JSON['workspaceToJson'] = Blockly.JSON.workspaceToJson;
