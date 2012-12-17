#!/bin/sh

# How to stress :
# Configure cron plugin : delay-stat = 3, delay-sensor = 30
# Start cron and earth plugins
# Create about 10 cron jobs using the UI. Add some interval ones to every 30s or 1minute
# And finally : ./stress.sh 10

LOG=plugins_test.log

COUNT=$1
[ -z $COUNT ] && COUNT=5

rm $LOG 2>/dev/null

I=0
while [ $I -lt $COUNT ] ; do
    ./run.sh
    I=`echo "$I + 1" | bc`
    #echo $I
done

grep -A 6 -B 1 "FAIL:" $LOG
grep -A 8 -B 1 "ERROR:" $LOG

OK=`grep -c ok $LOG` 2>/dev/null
echo "OK : " $OK
SK=`grep -c skipped $LOG` 2>/dev/null
echo "Skipped : " $SK
FA=`grep -c "FAIL:" $LOG` 2>/dev/null
echo "Failed : " $FA
ER=`grep -c "ERROR:" $LOG` 2>/dev/null
#~ ER=20
echo "Error : " $ER
#~ echo "Score : " `echo "( 1 - ( ( $ER + $FA ) / $OK ) ) * 100" | bc`
#~ echo "Absolute score : " `echo "( 1 - ( ( $ER + $FA + $SK ) / $OK ) ) * 100" | bc`
echo Done
