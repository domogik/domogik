<?php

class SiteController extends Controller
{
	/**
	 * Declares class-based actions.
	 */
	public function actions()
	{
		return array(
			// page action renders "static" pages stored under 'protected/views/site/pages'
			// They can be accessed via: index.php?r=site/page&view=FileName
			'page'=>array(
				'class'=>'CViewAction',
			),
		);
	}

    function updateNfo($path, $msg) {
        if (!file_put_contents ($path . "/update.nfo" , $msg, FILE_APPEND))
            throw new CHttpException(403,"Error writing " . $filename);            
	}

    private function listDir($name, $detail) {
        $dir = Yii::app()->file->set($detail['path'], true);
	    if (!$dir->exists)
            throw new CHttpException(403,"Error opening directory " . $detail['path']);
        
        $packages = array();
        $files = $dir->getContents(false, 'tgz');
        if ($files) {
            foreach ($files as $filepath) {
                $file = Yii::app()->file->set($filepath);
                $package = array(
                    'repositoryid' => $name,
                    'repository' => $detail['label'],
                    'filename' => $file->basename,
                    'deployed' => false,
                    'date' => Yii::app()->dateFormatter->formatDateTime($file->timeModified,'medium',null),
                    'size' => $file->size,
                );
                $package['deployed'] = Yii::app()->file->set(substr($filepath, 0, -4) . ".xml", true)->exists;
                array_push($packages, $package);                        
            }            
        }
        return $packages;
	}
    
    private function repositoryUpdate($name, $detail) {
        $repositories = array();
        if (($name != 'sas') && ($name != 'trash')) {
            $file = Yii::app()->file->set($detail['path'] . '/packages.lst', true);
            if ($file->exists) {
                $content = file_get_contents($file->realpath);
            } else {
                $content = '';
            }


            $file = Yii::app()->file->set($detail['path'] . '/update.nfo', true);
            if ($file->exists) {
                $update = file_get_contents($file->realpath);
	        } else {
                $update = '';
            }
            

            $repository = array(
                'id' => $name,
                'repository' => $detail['label'],
                'content' => $content,
                'update' => $update,
            );
            array_push($repositories, $repository);
        }
        return $repositories;
    }
    
    private function packageDeploy($repo, $package)
	{
        $srcDir = yii::app()->params['repositories'][$repo]['path'];
	    exec(YiiBase::getPathOfAlias('application.shellscripts') . "/drm-deploy.sh " . $srcDir . " " . substr($package, 0, -4), $results, $return);
	    if ($return == 0) {
	       $this->updateNfo($srcDir, "Package " . $package . " deployed in " . $repo);
	    }
        $str = '<ul>';
        foreach ($results as $result) {
            $str .= '<li>' . $result . '</li>';
        }
        $str .= '</ul>';
        
        Yii::app()->user->setFlash(($return == 0) ? 'info' : 'error', $str);            
    }
    
    private function packageMove($repo, $package, $destination)
	{
        if ($destination) {
            $srcpath = yii::app()->params['repositories'][$repo]['path'];
            $destpath = yii::app()->params['repositories'][$destination]['path'];
            $srcfile = Yii::app()->file->set($srcpath . '/' . $package, true);
            if ($srcfile->exists) {
                $srcfile->move($destpath . '/' . $package);
                $xmlfile = Yii::app()->file->set($srcpath . '/' . substr($package, 0, -4) . ".xml", true);
                if ($xmlfile->exists && $xmlfile->delete()) {
                    Yii::app()->user->setFlash('info',"Package " . $package . " moved to " . yii::app()->params['repositories'][$destination]['label']);                                
                } else {
                    Yii::app()->user->setFlash('error',"Package " . $package . " moved to " . yii::app()->params['repositories'][$destination]['label']. " but xml file was not deleted");                
                }
                
                updateNfo($srcDir, "Package " . $package . " moved to " . $destination);
	            if ($destination != 'trash') updateNfo($destDir, "Package " . $package . " moved from " . $repo);
            } else {
                Yii::app()->user->setFlash('error',"Error while moving package to " . yii::app()->params['repositories'][$destination]['label']);            
            }
        }
        $this->redirect(array('site/index'));   
    }
    
	/**
	 * This is the default 'index' action that is invoked
	 * when an action is not explicitly requested by users.
	 */
	public function actionIndex()
	{
        $packageUpload=new PackageUpload;
        $packages = array();
        $packageslst = array();
        $repositories = array();
        foreach (yii::app()->params['repositories'] as $name => $detail) {
    	    $packages = array_merge($packages, $this->listDir($name, $detail));
    	    $packageslst = array_merge($packageslst, $this->repositoryUpdate($name, $detail));
            if ($name != 'trash' && $name != 'sas') {
                $repositories[$name] = $detail['label'];
            }
        }
        $dataPackages=new CArrayDataProvider($packages, array(
            'keyField'=>'filename',
        ));
        $dataPackageslst=new CArrayDataProvider($packageslst, array(
            'keyField'=>'repository',
        ));
		$this->render('index', array('packages'=>$dataPackages,
                        'packageUpload'=>$packageUpload,
                        'packageslst'=>$dataPackageslst,
                        'repositories'=>$repositories));
	}

	public function actionPackageView($repo, $package)
	{
        $srcpath = yii::app()->params['repositories'][$repo]['path'];
        $package = substr($package, 0, -4);
        $xmlfile = Yii::app()->file->set($srcpath . '/' . $package . ".xml", true);
        if ($xmlfile->exists) {
            $content = file_get_contents($xmlfile->realpath);
        } else {
            $content = "No Data";
        }
		$this->render('packageView', array('package'=>$package,
                        'xml'=>$content));
    }
    
	public function actionPackageUpload()
	{
        $packageUpload=new PackageUpload;
        if(isset($_POST['PackageUpload']))
        {
            $packageUpload->attributes=$_POST['PackageUpload'];
            $packageUpload->package=CUploadedFile::getInstance($packageUpload,'package');
            if($packageUpload->validate())
            {
                $packageUpload->package->saveAs(yii::app()->params['repositories']['sas']['path'] . "/" . $packageUpload->package->getName());
                Yii::app()->user->setFlash('info',"The target file was successfully uploaded!");                                
            } else {
                Yii::app()->user->setFlash('error',"Error uploading target file!");                   
	        }
        }
        $this->redirect(array('site/index'));   
    }

    public function actionPackagesAction() {
        if(isset($_POST['packages']))
		{
            foreach (yii::app()->params['repositories'] as $repo => $detail) {
                if ($repo != 'trash' && isset($_POST['packages'][$repo])) {
                    foreach ($_POST['packages'][$repo]  as $package) {
                        if(isset($_POST['deploy']))
                            $this->packageDeploy($repo, $package);
                        if(isset($_POST['delete']))
                            $this->packageMove($repo, $package, 'trash');
                        if(isset($_POST['move']))
                            $this->packageMove($repo, $package, $_POST['destination']);
                    }
                }
            }
        }
        $this->redirect(array('site/index'));
    }
    
    public function actionPackagelstGenerate()
    {
        if(isset($_POST['package_list']))
        {
            $srcDir = yii::app()->params['repositories'][$_POST['package_list']]['path'];
	        exec(YiiBase::getPathOfAlias('application.shellscripts') . "/drm-generate-pkg-list.sh " . $srcDir, $results, $return);
            $str = '<ul>';
            foreach ($results as $result) {
                $str .= '<li>' . $result . '</li>';
            }
            $str .= '</ul>';
            Yii::app()->user->setFlash(($return == 0) ? 'info' : 'error', $str);
	
            $file = Yii::app()->file->set($srcDir . '/update.nfo', true);
            if ($file->exists && !$file->delete()) {
                Yii::app()->user->setFlash('error2',"update.nfo couldn't be deleted");                
            }
        }
        $this->redirect(array('site/index'));   
    }
    
	/**
	 * This is the action to handle external exceptions.
	 */
	public function actionError()
	{
	    if($error=Yii::app()->errorHandler->error)
	    {
	    	if(Yii::app()->request->isAjaxRequest)
	    		echo $error['message'];
	    	else
	        	$this->render('error', $error);
	    }
	}

	/**
	 * Displays the login page
	 */
	public function actionLogin()
	{
		$model=new LoginForm;

		// if it is ajax validation request
		if(isset($_POST['ajax']) && $_POST['ajax']==='login-form')
		{
			echo CActiveForm::validate($model);
			Yii::app()->end();
		}

		// collect user input data
		if(isset($_POST['LoginForm']))
		{
			$model->attributes=$_POST['LoginForm'];
			// validate user input and redirect to the previous page if valid
			if($model->validate() && $model->login())
				$this->redirect(Yii::app()->user->returnUrl);
		}
		// display the login form
		$this->render('login',array('model'=>$model));
	}

	/**
	 * Logs out the current user and redirect to homepage.
	 */
	public function actionLogout()
	{
		Yii::app()->user->logout();
		$this->redirect(Yii::app()->homeUrl);
	}
}