#!/bin/bash -e 
# The -e option will make the bash stop if any command raise an error ($? != 0)

source /home/travis/virtualenv/python2.7/bin/activate

# AS of 7/01/2015 this should not be needed anymore
#/etc/init.d/domogik-mq start
#sleep 10
/etc/init.d/domogik start
sleep 10
cat /var/log/domogik/core_manager.log

# for some plugins tests, the conversion functions may need to be imported, so we need the following line
export PYTHONPATH=/var/lib/domogik
