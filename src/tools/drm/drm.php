<?

include 'drm-config.php';


/**** Functions *************************/
function update($path, $msg) {
    $file = fopen($path . "/update.nfo", "a");
    fwrite($file, $msg . "\n");
    fclose($file);
}

function listDir($name, $path) {
    global $thisPhpFileName;
    global $repositoryList;
    global $sasName;
    global $trashName;
    if ($name == $sasName) {
        $class = "sas";
    }
    else if ($name == $trashName) {
        $class = "trash";
    }
    else {
        $class = "std";
    }
    if (@!$dir = opendir($path)) {
        echo "<div class='error'>Error opening directory " . $path . "</div>";
        return;
    }
    while ($f = readdir($dir)) {
        if (is_file($path . "/" . $f)) {
            if (substr($f, -4, 4) == ".tgz") {
                $fXml = substr($f, 0, -4) . ".xml";
                // statistics
                echo "<tr class='" . $class . "'>";
                echo "<td>" . $name . "</td>";
                echo "<td>";
                echo "<span class='package'>" . $f . "</span>";
                if (is_file($path . "/" . $fXml)) {
                    echo "<br/><span class='xml'>" . $fXml . "</span>";
                }
                else if (($sasName != $name) && ($trashName != $name)) {
                    echo "<form action='" . $thisPhpFileName . "' method='post' class='deploy'>";
                    echo "<input type='hidden' name='package' value='" . $f . "'/>";
                    echo "<input type='hidden' name='source' value='" . $name . "'/>";
                    echo "<input type='submit' name='deploy_package' value='Deploy package'/>";
                    echo "</form>";
                }
                echo "</td>";
                echo "<td>" . date ("F d Y H:i:s.", filemtime($path . "/" . $f)) . "</td>";
                echo "<td>" . filesize($path . "/" . $f) . "</td>";

                echo "<td>";
                echo "<form action='" . $thisPhpFileName . "' method='post'>";
                echo "<input type='hidden' name='package' value='" . $f . "'/>";
                echo "<input type='hidden' name='source' value='" . $name . "'/>";
                if ($trashName != $name) {
                    echo "<input type='submit' name='move' value='Move package to' />";
                    echo "<select name='target'>";
                    echo "<option selected>--</option>";
                    foreach ($repositoryList as $tmpRepoName => $tmpRepoPath) {
                        if (($name != $tmpRepoName) && ($trashName != $tmpRepoName)) {
                            echo "<option>" . $tmpRepoName . "</option>";
                        }
                    }
                    echo "</select>";
                    echo "<input type='submit' name='delete_package' value='Delete package' class='delete'/>";
                }
                echo "</form>";
                echo "</td>";
                echo "</tr>";
            }
        }
    }
    closedir($dir);
}
/****************************************/


?>

<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
<meta http-equiv="Content-Type" content="text/html; charset=iso-8859-1" />
<title>Repository sas</title>
<link rel="stylesheet" href="drm.css" type="text/css"/>
</head>
<body>
  <h1>Domogik Repositories Management</h1>

<?
/**** Traitement des actions ****/

// Upload file
if(@$_POST['send']){
        $uploadDir = $sasDir;
        $uploadFile = $uploadDir.basename($_FILES['package']['name']);
        if (move_uploaded_file($_FILES['package']['tmp_name'], $uploadFile)){
                echo "<div class='info'>The target file was successfully uploaded!</div>";
        }
        else{
                echo "<div class='error'>Error uploading target file!</div>";
        }
}

// Generate packages.lst
if(@$_POST['package_list']){
    if ($_POST['target'] != "--") {
        $srcDir = $repositoryList[$_POST['target']];
        exec("./drm-generate-pkg-list.sh " . $srcDir, $result, $return);
        if ($return == 0) {
            echo "<div class='info'>";
        }
        else {
            echo "<div class='error'>";
        }
        for($i=0;$i<sizeof($result);$i++) {
            echo $result[$i] . "<br/>";
        }
        echo "</div>";

        if (is_file($srcDir . "/update.nfo")) {
            if (!unlink($srcDir . "/update.nfo")) {
                echo "<div class='error'>update.nfo couldn't be deleted</div>";
            }
        }
    }
}

// Delete package
if(@$_POST['delete_package']){
    $destDir = $trashDir;
    $srcDir = $repositoryList[$_POST['source']];
    $package = $_POST['package'];
    if (rename($srcDir . "/" . $package, $destDir . "/" . $package)) {
        if (is_file($srcDir . "/" . substr($package, 0, -4) . ".xml")) {
            if (unlink($srcDir . "/" . substr($package, 0, -4) . ".xml")) {
                echo "<div class='info'>Package " . $package . " moved to " . $trashName . "</div>";
            }
            else {
                echo "<div class='error'>Package " . $package . " moved to " . $trashName . " but xml file was not deleted.</div>";
            }
        }
        else {
            echo "<div class='info'>Package " . $package . " moved to " . $trashName . "</div>";
       }
       update($srcDir, "Package " . $package . " moved to " . $trashName);
    }
    else {
        echo "<div class='error'>Error while moving package</div>";
    }
}

// Deploy package
if(@$_POST['deploy_package']){
    $srcDir = $repositoryList[$_POST['source']];
    $package = $_POST['package'];
    exec("./drm-deploy.sh " . $srcDir . " " . substr($package, 0, -4), $result, $return);
    if ($return == 0) {
        echo "<div class='info'>";
       update($srcDir, "Package " . $package . " deployed in " . $srcDir);
    }
    else {
        echo "<div class='error'>";
    }
    for($i=0;$i<sizeof($result);$i++) {
        echo $result[$i] . "<br/>";
    }
    echo "</div>";
}


// Move package to a repository
if(@$_POST['move']){
    if ($_POST['target'] != "--") {
        $destDir = $repositoryList[$_POST['target']];
        $srcDir = $repositoryList[$_POST['source']];
        $package = $_POST['package'];
        if (rename($srcDir . "/" . $package, $destDir . "/" . $package)) {
            if (is_file($srcDir . "/" . substr($package, 0, -4) . ".xml")) {
                if (unlink($srcDir . "/" . substr($package, 0, -4) . ".xml")) {
                    echo "<div class='info'>Package " . $package . " moved to " . $_POST['target'] . "</div>";
                }
                else {
                    echo "<div class='error'>Package " . $package . " moved to " . $_POST['target'] . " but xml file was not deleted.</div>";
                }
            }
            else {
                echo "<div class='info'>Package " . $package . " moved to " . $_POST['target'] . "</div>";
            }
            update($srcDir, "Package " . $package . " moved to " . $destDir);
            update($destDir, "Package " . $package . " moved from " . $srcDir);
        }
        else {
            echo "<div class='error'>Error while moving package</div>";
        }
    }
}
?>

  <div id='upload' class='section'>
    <h2>Upload package</h2>
     <div class='content'>
       <form enctype="multipart/form-data" action="<? echo $thisPhpFileName; ?>" method="post">
        <input type="hidden" name="MAX_FILE_SIZE" value="20000" />
        <p>Package to upload : <input name="package" type="file" /></p>
        <input type="submit" name="send" value="Upload Package" />
      </form>
    </div>
  </div>
  <div id='packagesList' class='section'>
    <h2>Packages.lst</h2>
    <div class='content'>
      <form action="<? echo $thisPhpFileName; ?>" method="post">
        <input type="submit" name="package_list" value="Generate 'packages.lst' for :"/>
<?
        echo "<select name='target'>";
        echo "<option selected>--</option>";
        foreach ($repositoryList as $tmpRepoName => $tmpRepoPath) {
            if (($sasName != $tmpRepoName) && ($trashName != $tmpRepoName)) {
                echo "<option>" . $tmpRepoName . "</option>";
            }
        }
        echo "</select>";
?>
      </form>
<?
    foreach ($repositoryList as $tmpRepoName => $tmpRepoPath) {
        if (($sasName != $tmpRepoName) && ($trashName != $tmpRepoName)) {
            echo "<div class='repository'>";
            echo "<h3>";
            echo "<span>" . $tmpRepoName . "</span>";
            echo "</h3>";
            $update = "n/a";
            if (is_file($tmpRepoPath . "/update.nfo")) {
                $class = "updated";
                if (!@$tabFile = file($tmpRepoPath . "/update.nfo")) {
                    $update = "n/a";
                }
                else {
                    $update = "";
                    for($i=0;$i<sizeof($tabFile);$i++) {
                        $update .= $tabFile[$i]; 
                    }
                }
            }
            else {
                $class = "std";
            }
            if (!@$tabFile = file($tmpRepoPath . "/packages.lst")) {
                $content = "n/a";
            }
            else {
                $content = "";
                for($i=0;$i<sizeof($tabFile);$i++) {
                    $content .= $tabFile[$i]; 
                }
            }
            echo "<pre class='$class'>" . $content . "</pre>";
            if ($update != "n/a") {
                echo "<h4>Updates : </h4>";
                echo "<pre class='updated'>" . $update . "</pre>";
            }
            echo "</div>";
        }
    }
    
?>
    </div>
  </div>
  <div id='list' class='section'>
    <h2>Packages list</h2>
    <div class='content'>
    <table>
      <thead>
        <tr>
          <th>Repository</th>
          <th>Filename</th>
          <th>Date</th>
          <th>Size</th>
          <th>Move / delete</th>
        </tr>
      </thead>
      <tbody>
<?

/**** Display repositories files ****/
foreach ($repositoryList as $name => $path) {
    listDir($name, $path);
}

?>
      </tbody>
    </table>
    </div>
  </div>
</body>
</html>
