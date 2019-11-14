#!/bin/bash -e
# The -e option will make the bash stop if any command raise an error ($? != 0)

#sleep 10
echo "==== START DOMOGIK"
# notice : we use <env> with set PATH because a virtualenv is used in Travis.
# If we don't set these flags, these actions will fail,
# the python packages (domogik) in virtualenv won't be find!
sudo env "PATH=$PATH VIRTUAL_ENV=$VIRTUAL_ENV" /etc/init.d/domogik start
sleep 10
cat /var/log/domogik/core_manager.log

# for some plugins tests, the conversion functions may need to be imported, so we need the following line
export PYTHONPATH=/var/lib/domogik
