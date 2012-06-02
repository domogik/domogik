#!/bin/bash

### parameters
if [[ $# -ne 1 ]] ; then
    echo "Usage : $0 <path to firmware : gceip*.hex>"
    exit 1
fi

### Check user action
firmware=$(basename $1)
echo "You are about to update IPX800 board with this firmware :"
echo "- $firmware"
echo "[Enter] to continue. [ctrl]-[c] to abort."
read

### remove "windows" carriage return
TEMP_FIRM=/tmp/$firmware
sed "s///" $1 > $TEMP_FIRM

### Flash ipx board
echo "Manual operations to do before hitting [enter] to flash board :"
echo "1. Check your computer ip is on 192.168.1.x network"
echo "2. Unplug board." 
echo "3. Wait a few minutes."
echo "4. While plug in board, press [enter]"
read

echo "Start updating..."
cd /tmp
tftp 192.168.1.159 <<!
put $TEMP_FIRM
!

### clean
rm -f $TEMP_FIRM

