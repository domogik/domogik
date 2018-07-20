#!/bin/bash 
# The -e option will make the bash stop if any command raise an error ($? != 0)

echo ""
echo "********** Processes *************"
ps -ef | grep dmg
ps -ef | grep admin
if [ ! -z $DMG_PLUGIN ] ; then 
    ps -ef | grep $DMG_PLUGIN
    echo "********** /var/log/domogik/plugin_$DMG_PLUGIN.log *******************"
    cat /var/log/domogik/plugin_$DMG_PLUGIN.log
fi

echo ""
echo "********** Gunicorn *************"
which gunicorn

echo ""
echo "********** List of logs file **********************"
ls -l /var/log/domogik/

for fic in /etc/default/domogik /etc/domogik/domogik.cfg /var/log/domogik/db_api.log /var/log/domogik/core_manager.log /var/log/domogik/core_xplgw.log /var/log/domogik/mq_broker.log /var/log/xplhub/bandwidth.csv /var/log/xplhub/client_list.txt /var/log/xplhub/invalid_data.csv /var/log/xplhub/xplhub.log /var/log/domogik/core_admin.log
  do
    echo ""
    echo "********** $fic *******************"
    echo ""
    cat $fic
    echo ""
done

