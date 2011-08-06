<?php
class MyFormatter extends CFormatter {
    
    public function formatBooleanIcon($value) {
        return $value ? CHtml::tag('div', array('class'=>'icon16 icon16-true'), CHtml::tag('span', array('class'=>'offscreen'), "Yes")) : CHtml::tag('div', array('class'=>'icon16 icon16-false'), CHtml::tag('span', array('class'=>'offscreen'), "No"));
    }    
}
?>