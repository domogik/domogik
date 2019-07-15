#!/bin/bash -e 
# The -e option will make the bash stop if any command raise an error ($? != 0)

mysql -e 'create database domogik;'
mysql -e "USE mysql;\nUPDATE user SET authentication_string=PASSWORD('domopass') where User='root'; \nUPDATE user SET plugin='mysql_native_password';FLUSH PRIVILEGES;"
mysql_upgrade -u root -pdomopass
service mysql restart

