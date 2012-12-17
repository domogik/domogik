#!/bin/sh

LOG=plugins_test.log

./cron/cron_test.py >>$LOG 2>>$LOG
./cron/cronquery_test.py >>$LOG 2>>$LOG

./earth/earth_test.py >>$LOG 2>>$LOG

#grep -A 5 -B 5 FAILED $LOG

echo Done
