#!/bin/bash -e 
# The -e option will make the bash stop if any command raise an error ($? != 0)

wget https://raw.githubusercontent.com/domogik/domogik-installation/master/install-develop.sh -O /tmp/install.sh
chmod +x /tmp/install.sh
export
VENV=$VIRTUAL_ENV
sudo su
source VENV/bin/activate
/tmp/install.sh

echo "==== SOME CLEANUP stuff"
sudo chown $LOGNAME:root /var/lock/domogik
sudo chown $LOGNAME:root /var/lock/domogik/config.lock
