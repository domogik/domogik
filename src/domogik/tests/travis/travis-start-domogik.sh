#!/bin/bash -e 
# The -e option will make the bash stop if any command raise an error ($? != 0)

which dmg_hub
which dmg_broker
which dmg_forwarder
sudo /etc/init.d/domogik start
sleep 10
cat /var/log/domogik/manager.log

