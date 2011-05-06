<?php
class PackageUpload extends CFormModel
{
    public $package;
 
    public function rules()
    {
        return array(
            array('package', 'file', 'types'=>'tgz'),
        );
    }
    
    /**
	 * Declares attribute labels.
	 */
	public function attributeLabels()
	{
		return array(
			'package'=>'Package to upload',
		);
	}
}
?>