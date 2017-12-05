#!/bin/bash -e 
# The -e option will make the bash stop if any command raise an error ($? != 0)

echo "==== Source virtualenv"
source $VENV/bin/activate

echo "==== Running install"
/tmp/install.sh

echo "==== SOME CLEANUP stuff"
chown $LOGNAME:root /var/lock/domogik
chown $LOGNAME:root /var/lock/domogik/config.lock
