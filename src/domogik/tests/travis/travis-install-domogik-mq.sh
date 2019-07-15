#!/bin/bash -e 
# The -e option will make the bash stop if any command raise an error ($? != 0)

echo "==== SOME SETUP stuff"
sudo mkdir -p /var/lock/domogik
sudo chown $LOGNAME:root /var/lock/domogik
sudo touch /var/lock/domogik/config.lock
sudo chown $LOGNAME:root /var/lock/domogik/config.lock

echo "==== Downloading domogik-mq"
wget https://github.com/domogik/domogik-mq/archive/develop.zip
unzip develop.zip
cd domogik-mq-develop

echo "==== RUNNING SETUP.py"
pip install .

echo "==== RUNNING pip install -r requirements.txt"
pip install -r requirements.txt

echo "==== RUNNING INSTALL.py"
sudo python install.py --no-setup --no-test --user $LOGNAME --command-line --daemon

echo "==== SOME CLEANUP stuff"
cd ..
sudo chown $LOGNAME:root /var/lock/domogik
sudo chown $LOGNAME:root /var/lock/domogik/config.lock
#sudo chown $LOGNAME:root /var/log/domogik/*
ls -l /var/lock/domogik/


