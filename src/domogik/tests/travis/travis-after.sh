#!/bin/bash -e 
# The -e option will make the bash stop if any command raise an error ($? != 0)

ps -ef | grep dmg
if [ ! -z $TUTUXX ] ; then 
    ps -ef | grep $DMG_PLUGIN
    echo "********** /var/log/domogik/$DMG_PLUGIN.log *******************"
    cat /var/log/domogik/$DMG_PLUGIN.log
fi


for fic in /etc/default/domogik /etc/domogik/domogik.cfg /var/log/domogik/db_api.log /var/log/domogik/dbmgr.log /var/log/domogik/manager.log /var/log/domogik/rest.log /var/log/domogik/xplgw.log /var/log/domogik/mq_broker.log /var/log/xplhub/bandwidth.csv /var/log/xplhub/client_list.txt /var/log/xplhub/invalid_data.csv /var/log/xplhub/xplhub.log
  do
    echo ""
    echo "********** /etc/default/domogik *******************
    echo ""
    cat $fic
    echo ""
done

