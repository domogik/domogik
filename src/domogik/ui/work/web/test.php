<blockquote>
<pre>



<?php

echo phpinfo();

if (isset($_POST)) {
    echo 'Contenu de $_POST<br />';
	
    print_r ($_POST);
	echo json_encode($_POST);
	
    echo 'Contenu JSON (json_decode)<br />';
    print_r ($_POST["json"], true);
}
else {
    echo "Rien re&ccedil;u !!!";
}
?>
</pre>
</blockquote>
