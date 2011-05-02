<div class='repository'>
    <h3><?php echo $data['repository']; ?></h3>
    <pre class='<?php ($data['update']) ? 'updated' : 'std'; ?>'><?php echo $data['content']; ?></pre>
    <?php
        if ($data['update']) {
            echo "<h4>Updates : </h4>";
            echo "<pre class='updated'>" . $data['update'] . "</pre>";
	    }
    ?>
</div>