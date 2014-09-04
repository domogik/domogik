#!/bin/bash -e 
# The -e option will make the bash stop if any command raise an error ($? != 0)

source /home/travis/virtualenv/python2.7/bin/activate

# TODO : remove, for debug only

echo "==== /etc/profile.d/gvm.sh ===="
cat /etc/profile.d/gvm.sh
echo "\n\n\n"
echo "==== /etc/init.d/domogik-mq ===="
cat /etc/init.d/domogik-mq
echo "\n\n\n"
echo "==== /home/travis/.nvm/current ===="
ls -l /home/travis/.nvm/current
echo "\n\n\n"
echo "==== /var/lock/domogik/ ===="
ls -l /var/lock/domogik/
ls -ld /var/lock/domogik/
echo "\n\n\n"
echo "==== /etc/passwd ===="
cat /etc/passwd
echo "\n\n\n"
# TODO END

/etc/init.d/domogik-mq start
sleep 10
/etc/init.d/domogik start
sleep 10
cat /var/log/domogik/manager.log

