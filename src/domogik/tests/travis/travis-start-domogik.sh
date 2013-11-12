#!/bin/bash -e 
# The -e option will make the bash stop if any command raise an error ($? != 0)

sudo /etc/init.d/domogik start
sleep 10
cat /var/log/domogik/manager.log

