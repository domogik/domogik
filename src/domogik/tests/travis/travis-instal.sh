#!/bin/bash -e 
# The -e option will make the bash stop if any command raise an error ($? != 0)

echo "==== SOME SETUP stuff"
sudo mkdir -p /var/lock/domogik
sudo chown $LOGNAME:root /var/lock/domogik
sudo touch /var/lock/domogik/config.lock
sudo chown $LOGNAME:root /var/lock/domogik/config.lock

echo "==== RUNNING installer"
wget https://raw.githubusercontent.com/domogik/domogik-installation/master/install-develop.sh -O install.sh
chmod +x install.sh
sudo ./install.sh

echo "==== SOME CLEANUP stuff"
sudo chown $LOGNAME:root /var/lock/domogik
sudo chown $LOGNAME:root /var/lock/domogik/config.lock
#sudo chown $LOGNAME:root /var/log/domogik/*
ls -l /var/lock/domogik/


