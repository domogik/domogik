#!/bin/bash -e
# The -e option will make the bash stop if any command raise an error ($? != 0)

# No needed, allready activate by travis
#echo "=== Start virtualenv dmg_==="
#source /home/travis/virtualenv/python$PYTHON_VER/bin/activate

#sleep 10
echo "==== START DOMOGIK"
/etc/init.d/domogik start
sleep 10
cat /var/log/domogik/core_manager.log

# for some plugins tests, the conversion functions may need to be imported, so we need the following line
export PYTHONPATH=/var/lib/domogik
