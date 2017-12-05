#!/bin/bash -e 
# The -e option will make the bash stop if any command raise an error ($? != 0)

echo "==== Downloading and preparing the install script"
wget https://raw.githubusercontent.com/domogik/domogik-installation/master/install-develop.sh -O /tmp/install.sh
chmod +x /tmp/install.sh

echo "==== Copy over the virtual env to root"
export
VENV=$VIRTUAL_ENV
echo $VENV

echo "==== Launch the installer"
sudo "sh $VENV/bin/activate; /tmp/install.sh"

echo "==== SOME CLEANUP stuff"
sudo chown $LOGNAME:root /var/lock/domogik
sudo chown $LOGNAME:root /var/lock/domogik/config.lock
