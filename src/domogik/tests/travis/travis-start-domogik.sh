#!/bin/bash -e 
# The -e option will make the bash stop if any command raise an error ($? != 0)

source /home/travis/virtualenv/python3.6/bin/activate

# For debuging travis-ci entry_points
echo "==== CHECK entry_points"
echo "login: "$LOGNAME
PATH=$PATH:~/local/bin
echo "PATH: "$PATH
echo "==== ls -l ~/.local"
ls -l ~/local/bin
echo "which dmg_hub :"
which dmg_hub
cat /home/travis/virtualenv/python3.6.7/bin/dmg_hub

#sleep 10
echo "==== START DOMOGIK"
/etc/init.d/domogik start
sleep 10
cat /var/log/domogik/core_manager.log

# for some plugins tests, the conversion functions may need to be imported, so we need the following line
export PYTHONPATH=/var/lib/domogik
