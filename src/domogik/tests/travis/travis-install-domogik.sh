#!/bin/bash -e 
# The -e option will make the bash stop if any command raise an error ($? != 0)

sudo mkdir -p /var/lock/domogik
sudo chown $LOGNAME:root /var/lock/domogik
sudo touch /var/lock/domogik/config.lock
sudo chown $LOGNAME:root /var/lock/domogik/config.lock
python setup.py install
sudo python install.py --no-setup True --user $LOGNAME --command-line --domogik_log_level debug --domogik_bind_interface 127.0.0.1 --database_name domogik --database_user travis --rest_interfaces lo --rest_clean_json True --mq_ip 127.0.0.1 --hub_interfaces lo --hub_log_level info --hub_log_bandwidth True --hub_log_invalid_data True
sudo chown $LOGNAME:root /var/lock/domogik
sudo chown $LOGNAME:root /var/lock/domogik/config.lock
sudo chown $LOGNAME:root /var/log/domogik/*
ls -l /var/lock/domogik/

