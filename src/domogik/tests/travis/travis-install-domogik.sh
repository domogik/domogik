#!/bin/bash -e
# The -e option will make the bash stop if any command raise an error ($? != 0)

echo "==== SOME SETUP stuff"
PIDDIR="/var/run/domogik"
LOCKDIR="/var/lock/domogik"
LOGDIR="/var/log/domogik"
CACHEDIR="/var/cache/domogik"
sudo mkdir -p $LOCKDIR
sudo chown $LOGNAME:root $LOCKDIR
sudo touch $LOCKDIR/config.lock
sudo chown $LOGNAME:root $LOCKDIR/config.lock
sudo mkdir -p $PIDDIR
sudo chown $LOGNAME: $PIDDIR
sudo mkdir -p $LOGDIR
sudo chown $LOGNAME: $LOGDIR
sudo mkdir -p $CACHEDIR
sudo chown $LOGNAME: $CACHEDIR
sudo mkdir -p /var/lib/domogik
sudo chown $LOGNAME: /var/lib/domogik
sudo mkdir -p /var/log/xplhub
sudo chown $LOGNAME: /var/log/xplhub
sudo mkdir -p /etc/domogik
sudo chown $LOGNAME: /etc/domogik
sudo mkdir -p /etc/logrotate.d
sudo chown $LOGNAME: /etc/logrotate.d
sudo mkdir -p /etc/systemd/system
sudo chown $LOGNAME: /etc/systemd/system
sudo mkdir -p /etc/init.d
sudo chown $LOGNAME: /etc/init.d
sudo mkdir -p /etc/rc.d
sudo chown $LOGNAME: /etc/rc.d
sudo mkdir -p /etc/cron.d
sudo chown $LOGNAME: /etc/cron.d

echo "==== RUNNING SETUP.py"
pip3 install .
pip3 freeze
echo "==== RUNNING pip install -r requirements.txt"
pip3 install -r requirements.txt


echo "==== RUNNING INSTALL.py"
# notice : we use --no-setup and --no-db-upgrade because a virtualenv is used in Travis.
# If we don't set these flags, these actions will be done as root user and so,
# the python packages (domogik) in virtualenv won't be find!

python3 install.py --no-setup --no-test --no-db-upgrade --user $LOGNAME --command-line --domogik_log_level debug --domogik_bind_interface lo --database_name domogik --database_user travis --admin_interfaces lo --admin_clean_json True --hub_interfaces lo --hub_log_level info --hub_log_bandwidth True --hub_log_invalid_data True --no-mq-check --metrics_id travis_build

echo "==== RUNNING DB_INSTALL.py"
python3 src/domogik/install/db_install.py

echo "==== SOME CLEANUP stuff"
sudo chown $LOGNAME:root /var/lock/domogik
sudo chown $LOGNAME:root /var/lock/domogik/config.lock
#sudo chown $LOGNAME:root /var/log/domogik/*
ls -l /var/lock/domogik/
