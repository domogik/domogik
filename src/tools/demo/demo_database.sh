#!/bin/bash
#
# Script for moving actual sqlite base and creating a new one
#
# This works only for sqlite db
#


db_type=$(grep db_type ~/.domogik.cfg | cut -d"=" -f2 -s | sed "s/ //g")
db_path=$(grep db_path ~/.domogik.cfg | cut -d"=" -f2 -s | sed "s/ //g")
timestamp=$(date +"%Y%m%d-%H%M")
file_in=./demo-data.txt


### Parameters
if [[ $# -eq 0 ]] ; then
    ip=127.0.0.1
    port=8080
fi
if [[ $# -ge 1 ]] ; then
    ip=$1
fi
if [[ $# -eq 2 ]] ; then
    port=$2
fi
if [[ $# -eq 3 ]] ; then
    file_in=$3
fi

echo "Databse type : '$db_type'"
if [[ $db_type != "sqlite" ]] ; then
    echo "This script works only for sqlite database"
    exit 1
fi 



### Check REST is up
echo ""
echo ""
echo "REST module will be killed and restarted after operation."
echo "You may also have to restart UI"
echo "Continue ? [Y/N]"
read choice

if [[ $choice != "Y" ]] ; then
    echo "Exiting..."
    exit 1
fi




### Kill REST module
echo ""
echo ""
echo "Killing REST module..."
killall -9 rest.py
echo "...ok"




### Move actual database
echo ""
echo ""
echo "Move $db_path to $db_path.$timestamp..."
mv $db_path $db_path.$timestamp
if [[ $? -ne 0 ]] ; then
    echo "Error... exiting."
    exit 1
fi
echo "...ok"


### Create new database
echo ""
echo ""
echo "Creating new database..."
python ../../../db_installer.py 
if [[ $? -ne 0 ]] ; then
    echo "Error... exiting."
    exit 1
fi
echo "...ok"



### Start REST module
echo ""
echo ""
echo "Starting REST module..."
nohup ../../domogik/xpl/lib/rest.py > /tmp/demo.log &
sleep 10
if [[ $? -ne 0 ]] ; then
    echo "Error... exiting."
    exit 1
fi
echo "...ok"




### Add data in database
echo ""
echo ""
./call_rest.py

