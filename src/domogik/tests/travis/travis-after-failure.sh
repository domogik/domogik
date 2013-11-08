#!/bin/bash -e 
# The -e option will make the bash stop if any command raise an error ($? != 0)

ps -ef | grep dmg
ps -ef | grep $DMG_PLUGIN
cat /etc/default/domogik
cat /var/log/domogik/$DMG_PLUGIN.log
cat /var/log/domogik/db_api.log
cat /var/log/domogik/dbmgr.log
cat /var/log/domogik/manager.log
cat /var/log/domogik/rest.log
cat /var/log/domogik/xplgw.log
cat /var/log/domogik/mq_broker.log
cat /var/log/xplhub/bandwidth.csv
cat /var/log/xplhub/client_list.txt
cat /var/log/xplhub/invalid_data.csv
cat /var/log/xplhub/xplhub.log

