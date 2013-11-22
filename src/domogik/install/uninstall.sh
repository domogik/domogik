#!/bin/bash
#This file is part of B{Domogik} project (U{http://www.domogik.org}).
#
#License
#=======
#
#B{Domogik} is free software: you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.
#
#B{Domogik} is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#GNU General Public License for more details.
#
#You should have received a copy of the GNU General Public License
#along with Domogik. If not, see U{http://www.gnu.org/licenses}.
#
#Module purpose
#==============
#
#Clean domogik installation
#
#Implements
#==========
#
#
#@author: Fritz < fritz.smh@gmail.com>
#@copyright: (C) 2007-2012 Domogik project
#@license: GPL(v3)
#@organization: Domogik



function stop_domogik {
    if [ -f "/etc/init.d/domogik" -o -f "/etc/rc.d/domogik" ];then
        if [ -d "/var/run/domogik" ];then
            [ -f /etc/conf.d/domogik ] && . /etc/conf.d/domogik
            [ -f /etc/default/domogik ] && . /etc/default/domogik
            if [ -f "/etc/domogik/domogik.cfg" ];then
                echo "There is already a Domogik on this system. Try to stop it before uninstall..."
                /etc/init.d/domogik stop
            fi
        fi
    else
        echo "It seems Domogik is not installed : no /etc/init.d|rc.d/domogik file"
        exit 16
    fi
}


# IS root user ?
if [ $UID -ne 0 ];then
    echo "Please restart this script as root!"
    exit 10
fi

# Ask for confirmation
echo "This script will uninstall completely Domogik :"
echo "- Domogik core"
echo "- xPL hub"
echo "- Configuration"
echo "- Plugins"
echo "- Logs"
echo "- ..."
echo "Only the database will not be removed"
echo "Are you sure ? [y/N]"
read choice
if [ "x"$choice == "x" ] ; then
    choice=n
fi
if [ $choice != "y" -a $choice != "Y" ] ; then
    echo "Aborting..."
    exit 0
fi

stop_domogik

[ ! -f /etc/default/domogik ] && [ ! -f /etc/conf.d/domogik ] && echo "File /etc/default/domogik or /etc/conf.d/domogik doesn't exists : exiting" && exit 1

[ -f /etc/conf.d/domogik ] && . /etc/conf.d/domogik && GLOBAL_CONFIG=/etc/conf.d/domogik
[ -f /etc/default/domogik ] && . /etc/default/domogik && GLOBAL_CONFIG=/etc/default/domogik

echo "Domogik installation found for user : $DOMOGIK_USER"

#RM="ls -l "  # for simulation
RM="rm -Rf "

echo "Delete /etc/logrotate.d/domogik"
$RM /etc/logrotate.d/domogik
echo "Delete /etc/logrotate.d/xplhub"
$RM /etc/logrotate.d/xplhub

echo "Delete /etc/default/domogik"
$RM /etc/default/domogik

echo "Delete rc.d script"
[ -f /etc/init.d/domogik ] && $RM /etc/init.d/domogik
[ -f /etc/rc.d/domogik ] && $RM /etc/rc.d/domogik

echo "Delete /var/cache/domogik"
$RM /var/cache/domogik

echo "Delete /var/lib/domogik/resources"
$RM /var/lib/domogik/resources

echo "Delete /var/lock/domogik"
$RM /var/lock/domogik

CONFIG_FOLDER=/etc/domogik/
echo "Delete config folder : $CONFIG_FOLDER"
$RM $CONFIG_FOLDER

echo "Delete $GLOBAL_CONFIG"
$RM $GLOBAL_CONFIG

echo "Delete /var/log/domogik"
$RM /var/log/domogik
echo "Delete /var/log/xplhub"
$RM /var/log/xplhub

for fic in dmgenplug dmgdisplug dmg_manager dmg_send dmg_pkgmgr dmg_version dmg_dump dmg_hub 
  do
    TO_DEL=$(which $fic)
    if [ "X"$TO_DEL != "X" ] ; then
        echo "$(which $fic) / $TO_DEL"
        echo "Delete $TO_DEL"
        $RM $TO_DEL
    fi
done

PY_FOLDER=$(dirname $(python -c "print __import__('domogik').__path__[0]"))
if [[ ${PY_FOLDER:0:5} == "/usr/" ]] ; then
    echo "Remove python part : $PY_FOLDER"
    $RM $PY_FOLDER
else
    echo "Not removing $PY_FOLDER"
    echo "It seems to be development files"
fi

echo "Notice : database was not suppressed : you must do it manually"
echo "         the folder /var/lib/domogik/domogik_packages was not suppressed"

echo "Uninstall complete!"





