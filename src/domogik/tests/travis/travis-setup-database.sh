#!/bin/bash -e 
# The -e option will make the bash stop if any command raise an error ($? != 0)

mysql -e 'create database domogik;'
echo "USE mysql;\nUPDATE user SET password=PASSWORD('domopass') WHERE user='travis';\nFLUSH PRIVILEGES;\n" | mysql -u root

