#!/bin/bash -e 
# The -e option will make the bash stop if any command raise an error ($? != 0)

echo "==== SOME SETUP stuff"
sudo mkdir -p /var/lock/domogik
sudo chown $LOGNAME:root /var/lock/domogik
sudo touch /var/lock/domogik/config.lock
sudo chown $LOGNAME:root /var/lock/domogik/config.lock

echo "==== RUNNING SETUP.py"
#sudo python setup.py install
pip install .

echo "==== RUNNING INSTALL.py"
# notice : we use --no-setup and --no-db-upgrade because a virtualenv is used in Travis. 
# If we don't set these flags, these actions will be done as root user and so, 
# the python packages (domogik) in virtualenv won't be find!
sudo python install.py --no-setup --no-test --no-db-upgrade --user $LOGNAME --command-line --domogik_log_level debug --domogik_bind_interface 127.0.0.1 --database_name domogik --database_user travis --rest_interfaces lo --rest_clean_json True --mq_ip 127.0.0.1 --hub_interfaces lo --hub_log_level info --hub_log_bandwidth True --hub_log_invalid_data True

echo "==== RUNNING DB_INSTALL.py"
python src/domogik/install/db_install.py

echo "==== SOME CLEANUP stuff"
sudo chown $LOGNAME:root /var/lock/domogik
sudo chown $LOGNAME:root /var/lock/domogik/config.lock
#sudo chown $LOGNAME:root /var/log/domogik/*
ls -l /var/lock/domogik/

