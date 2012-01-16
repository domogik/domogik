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
#@copyright: (C) 2007-2009 Domogik project
#@license: GPL(v3)
#@organization: Domogik



function stop_domogik {
    if [ -d "/etc/init.d/" ];then
        if [ -f "/etc/init.d/domogik" ];then
            if [ -d "/var/run/domogik" ];then
                [ -f /etc/conf.d/domogik ] && . /etc/conf.d/domogik
                [ -f /etc/default/domogik ] && . /etc/default/domogik
                if [ -f "/home/${DOMOGIK_USER}/.domogik/domogik.cfg" ];then
                    echo "There is already a Domogik on this system. Try to stop it before uninstall..."
                    /etc/init.d/domogik stop
                fi
            fi
        fi
    elif [ -d "/etc/rc.d/" ];then
        echo "TODO"
    else
        echo "Init directory does not exist (/etc/init.d or /etc/rc.d)"
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
echo "- Configuration"
echo "- Plugins"
echo "- ..."
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

echo "Delete /etc/default/domogik"
$RM /etc/default/domogik

echo "Delete rc.d script"
[ -f /etc/init.d/domogik ] && $RM /etc/init.d/domogik
[ -f /etc/rc.d/domogik ] && $RM /etc/rc.d/domogik

echo "Delete /usr/local/share/domogik"
$RM /usr/local/share/domogik

CONFIG_FOLDER=/home/$DOMOGIK_USER/.domogik/
echo "Delete config folder : $CONFIG_FOLDER"
$RM $CONFIG_FOLDER

echo "Delete $GLOBAL_CONFIG"
$RM $GLOBAL_CONFIG

for fic in dmgenplug dmgdisplug dmg_manager dmg_send #TODO : DEL#dmg_django
  do
    TO_DEL=$(which $fic)
    echo "Delete $TO_DEL"
    $RM $TO_DEL
done

PY_FOLDER=$(dirname $(python -c "print __import__('domogik').__path__[0]"))
if [ ${PY_FOLDER:0:5} == "/usr/" ] ; then
    echo "Remove python part : $PY_FOLDER"
    $RM $PY_FOLDER
else
    echo "Not removing $PY_FOLDER"
    echo "It seems to be development files"
fi

echo "Notice : database was not suppressed : you must do it manually"

echo "Uninstall complete!"





