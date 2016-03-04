# first, start mysql
/usr/bin/mysqld_safe > /dev/null 2>&1 &

# wait a bit to be sure all is up. TODO : make a loop to check ports are open to be sure
echo "Wait for mysql to be up"
ready=no
while [ $ready == "no" ] ; do
    sleep 3
    cat < /dev/null > /dev/tcp/127.0.0.1/3306 
    if [ $? -eq 0 ] ; then
        ready=yes
    fi
    echo -n "."
done
echo ""

# start Domogik 
/etc/init.d/domogik start

# wait a bit to be sure all is up. TODO : make a loop to check ports are open to be sure
echo "Wait for Domogik to be up"
ready=no
while [ $ready == "no" ] ; do
    sleep 3
    cat < /dev/null > /dev/tcp/127.0.0.1/40406 
    if [ $? -eq 0 ] ; then
        ready=yes
    fi
    echo -n "."
done
echo ""

# start Domoweb
/etc/init.d/domoweb start

# display BIND informations
#grep BIND /var/log/domogik/*

# configure some packages and create some devices if the related script exists
su - domogik -c "[ -f /opt/dmg/post_install.py ] && /opt/dmg/post_install.py"

# display ready to use message
echo "  *****************"
echo "  * Domogik is up *"
echo "  *****************"

# run a bash
/bin/bash

# run an eternal loop
#while [ 1 -eq 1 ] ; do
#    echo "Alive since $SECONDS seconds..."
#    sleep 30
#done
