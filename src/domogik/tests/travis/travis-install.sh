#!/bin/bash -e 
# The -e option will make the bash stop if any command raise an error ($? != 0)

echo "==== SOME SETUP stuff"
mkdir -p /var/lock/domogik
chown $LOGNAME:root /var/lock/domogik
touch /var/lock/domogik/config.lock
chown $LOGNAME:root /var/lock/domogik/config.lock

echo "==== RUNNING installer"
wget https://raw.githubusercontent.com/domogik/domogik-installation/master/install-develop.sh -O /tmp/install.sh
chmod +x /tmp/install.sh
/tmp/install.sh

echo "==== SOME CLEANUP stuff"
chown $LOGNAME:root /var/lock/domogik
chown $LOGNAME:root /var/lock/domogik/config.lock
#sudo chown $LOGNAME:root /var/log/domogik/*
ls -l /var/lock/domogik/


