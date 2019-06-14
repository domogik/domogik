#!/bin/bash -e 
# The -e option will make the bash stop if any command raise an error ($? != 0)

source /home/travis/virtualenv/python2.7/bin/activate

# For debuging travis-ci entry_points
echo "==== CHECK entry_points"
echo "login: "$LOGNAME
echo "PATH: "$PATH
echo "which dmg_hub :"
which dmg_hub
ls -l /usr/local/bin
cat  cat /usr/local/bin/dmg_dump

#sleep 10
echo "==== START DOMOGIK"
/etc/init.d/domogik start
sleep 10
cat /var/log/domogik/core_manager.log

# for some plugins tests, the conversion functions may need to be imported, so we need the following line
export PYTHONPATH=/var/lib/domogik
