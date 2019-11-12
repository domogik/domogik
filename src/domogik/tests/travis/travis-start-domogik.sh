#!/bin/bash -e
# The -e option will make the bash stop if any command raise an error ($? != 0)

#sleep 10
echo "==== SEARCH dmg_hub"
which dmg_hub
sudo which dmg_hub
echo "==== START DOMOGIK"
sudo env "PATH=$PATH VIRTUAL_ENV=$VIRTUAL_ENV" /etc/init.d/domogik start
sleep 10
cat /var/log/domogik/core_manager.log

# for some plugins tests, the conversion functions may need to be imported, so we need the following line
export PYTHONPATH=/var/lib/domogik
