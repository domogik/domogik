#CFile for Yii Framework.
This extension offers commonly used functions for filesystem objects (files and directories) manipulation.

Project page
[http://github.com/idlesign/ist-yii-cfile](http://github.com/idlesign/ist-yii-cfile)

Report bugs to
[http://github.com/idlesign/ist-yii-cfile/issues](http://github.com/idlesign/ist-yii-cfile/issues)


###Properties
* exists
* isdir
* isfile
* isempty
* isuploaded
* readable
* writeable
* realpath
* basename (setter available)
* filename (setter available)
* dirname
* extension (setter available)
* mimeType
* timeModified
* size
* owner (setter available)
* group (setter available)
* permissions (setter available)

###Methods
* Create
* CreateDir
* Purge
* Contents
* Copy
* Rename/Move
* Send/Download
* Delete


#Changelog

###August 20, 2010
* 0.8
  * new: 'serverHandled' parameter in send() & download() methods allows sending [even huge] files with great speed
  * fix: be PHP 5.1+ compatible (proposed by heyhoo)
  * fix: permissions set incorrectly (spotted by heyhoo)

###June 16, 2010
* 0.7
  * new: 'flags' argument for setContents() method (proposed by TeKi)
  * fix: parameter type checks (for 'posix_getpwuid' & 'posix_getgrgid' functions) added to getOwner and getGroup methods (spotted by Spyros)


###December 8, 2009
* 0.6
  * new: set() method now supports Yii path aliases (proposed by Spyros)
  * chg: getContents() method now has 'filter' parameter to return filtered directory contents (regexp supported)
  * fix: undefined 'uploaded' variable in set() method (spotted by jerry2801)


###November 22, 2009
* 0.5
  * new: Uploaded files support (through CUploadedFile Yii class)
  * new: 'isUploaded' property
  * chg: getContents() method now has 'recursive' parameter for directories
  * fix: always recursive dirContents() method behaviour changed to appropriate


###November 3, 2009
* 0.4
  * new: 'isFile' & 'isDir' properties
  * new: rename(), move(), copy(), delete(), getSize() and getContents() methods now are able to deal with directories
  * new: purge() method to empty filesystem object
  * new: createDir() method to create directory
  * new: 'isEmpty' property
  * chg: 'formatPrecision' param of getSize() method now changed to 'format' and accepts format pattern for 'CNumberFormatter'
  * chg: download() method is now alias for primary send() method
  * chg: now 'readable' & 'writeable' properties are loaded on set() even when in non-greedy mode
  * fix: unnecessary file availability checks when 'greedy' option is specified for set() removed


###October 27, 2009
* 0.3
  * new: setBasename() method (lazy file rename)
  * new: setFilename() method (lazy file rename)
  * new: setExtension() method (lazy file rename)
  * new: download() method
  * chg: copy() & rename() methods improved (destination file name without path is enough for them to perform actions in the current file directory)
  * fix: 'extension' key existance check (in pathInfo())

###October 26, 2009
* 0.2
  * new: getContents() and setContents() methods
  * new: create() method
  * new: 'readable' & 'writeable' properties
  * fix: posix family functions existance check (in getOwner() & getGroup())

###October 25, 2009
* 0.1 Initial release.


#Documentation

###Requirements
Yii 1.0 or above

###Installation
Extract the release file under `protected/extensions/file`

###Usage
Introduce CFile to Yii.
Add definition to CWebApplication config file (main.php)

    'components'=>array(
        ...
        'file'=>array(
            'class'=>'application.extensions.file.CFile',
        ),
        ...
    ),

Now you can access CFile properties and methods as follows:

    $myfile = Yii::app()->file->set('files/test.txt', true);
    /*
      We use set() method to link new CFile object to our file
      First set() parameter - 'files/test.txt' - is the file path (here we supply
      relative path wich is automatically converted into real file path such as
      '/var/www/htdocs/files/test.txt').
      Second set() parameter - true - tells CFile to get all file properties at the
      very beginning (it could be omitted if we don't need all of them).
      $myfile now contains CFile object, let's see what do we got there
    */
    var_dump($myfile); // you may dump object to see all its properties

    echo $myfile->size; // or get property

    $myfile->permissions=755; // or set property

    $mynewfile = $myfile->copy('test2.txt'); // or manipulate file somehow, eg. copy
    // See CFile methods for actions available.

    /*
    Now $mynewfile contains new CFile object
    In this example file 'test2.txt' created in the same directory as our first 'test.txt' file
    */

    /* The following is also valid */
    if (Yii::app()->file->set('files/test3.txt')->exists)
        echo 'Bingo-bongo!';
    else
        echo 'No-no-no.';

    /*
    Since 0.5 you can manipulate uploaded files (through CUploadedFile Yii class).

    Let's suppose that we have the following form in our html:

      <form enctype="multipart/form-data" method="post">
        <input type="file" name="myupload"/>
        <input type="submit"/>
      </form>

    After the form is submitted we can handle uploaded file as usual.
    */
    $uploaded = Yii::app()->file->set('myupload');

    // Let's copy newly uploaded file into 'files' directory with its original name.
    $newfile = $uploaded->copy('files/'.$uploaded->basename);

    /*
    Since 0.6 you can use Yii path aliases.
    See http://www.yiiframework.com/doc/guide/basics.namespace for information
    about path aliases.

    Now let's get the contents of the directory where CFile resides
    (supposing that it is in Yii extensions path in the 'file' subdirectory).
    */
    $cfileDir = Yii::app()->file->set('ext.file');
    print_r($cfileDir->contents);

    /*
    Directory contents filtering was also introduced in 0.6.

    Futher we get all php files from $cfileDir mentioned above.
    We do not need all the decendants (recursion) so we supply 'false' as the first parameter
    for getContents() method.
    The second parameter describes filter, i.e. let me see only 'php' files.
    You can supply an array of rules (eg. array('php', 'txt')).
    NB: Moreover you can define perl regular expressions as rules.
    */
    print_r($cfileDir->getContents(false, 'php'));

    /*
    Since 0.8 you can boost up file downloads.
    Feature requires 'x-sendfile' header support from server (eg. Apache with mod_xsendfile or lighttpd).
    If CFile::download() second parameter ('serverHandled') is set to True file download uses server internals.
    */
    $myfile->download('myfastfile.txt', true);

###Usage hint
The other way to use this class is to import it into Yii:

    Yii::import('application.extensions.file.CFile');

    if (CFile::set('files/test3.txt')->exists)
        echo 'Bingo-bongo!';
    else
        echo 'No-no-no.';

###Further reading
Detailed information about class properties and methods could be found in CFile.php source code.