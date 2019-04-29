#!/bin/bash -e 
# The -e option will make the bash stop if any command raise an error ($? != 0)

mysql -e 'CREATE DATABASE domogik;'
sudo mysql -e "use mysql; update user set authentication_string=PASSWORD('domopass') where User='travis'; update user set plugin='mysql_native_password';FLUSH PRIVILEGES;"
sudo mysql_upgrade -u travis -pdomopass
echo "GRANT ALL PRIVILEGES ON domogik.* TO 'travis'@'%' WITH GRANT OPTION;\n" | mysql -u root
sudo service mysql restart
