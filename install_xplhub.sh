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
#Help to manage python xPL hub installation
#
#Implements
#==========
#
#
#@author: Fritz SMH <fritz.smh@gmail.com>
#@copyright: (C) 2007-2012 Domogik project
#@license: GPL(v3)
#@organization: Domogik
#
#TODO
#====
#
#Setup.py
#Init.d
#Actually, this install script is only used to create needed directories and configuration files


# Manage options

function display_usage {
    echo "Usage : "
    echo "  Full installation : ./install.sh"
    echo "  Help : ./install.sh -h"
    echo "         ./install.sh --help"
}

MAIN_INSTALL=y
while [ "$1" ] ; do 
    arg=$1
    case $arg in
        -h) 
            display_usage
            exit 0
            ;;
        --help) 
            display_usage
            exit 0
            ;;
        *) 
            display_usage
            exit 1
            ;;
    esac	
    shift
done


HUB_ETC=/etc/xplhub

#function test_sources {
#    FILENAME=$1
#    [ -d "$PWD/src" ] ||( echo "Can't find src/ directory, are you running this script from the sources main directory? (with ./$FILENAME" && exit 2 )
#    [ -f "src/xplhub/examples/config/xplhub.cfg" ] ||( echo "Can't find src/xplhub/examples/config/xplhub.cfg file!" && exit 3 )
#}

function copy_sample_files {
    read -p "Which user will run the xplhub, it will be created if it does not exist yet? (default : domogik) " d_user
    d_user=${d_user:-domogik}
    if ! getent passwd $d_user >/dev/null;then
        echo "I can't find informations about this user !"
        read -p "Do you want to create it ? (y/n) " create
        if [ "$create" = "y" ];then
            adduser $d_user
        else
            echo "Please restart this script when the user $d_user will exist."
            exit 9
        fi
    fi
    keep="n"
    already_cfg=
    # create /etc/xplhub entry
    if [ ! -d $HUB_ETC ];then
        mkdir $HUB_ETC
        chown $d_user:root $HUB_ETC
        chmod 755 $HUB_ETC
    fi
    if [ ! -f $HUB_ETC/xplhub.cfg ];then
        cp -f src/xplhub/examples/config/xplhub.cfg $HUB_ETC/xplhub.cfg
        chown $d_user:root $HUB_ETC/xplhub.cfg
        chmod 640 $HUB_ETC/xplhub.cfg
    else
        keep="y"
        already_cfg=1
        read -p "You already have xPL hub configuration files. Do you want to keep them ? [Y/n]" keep
        if [ "x$keep" = "x" ];then
            keep="y"
        fi
        if [ "$keep" = "n" -o "$keep" = "N" ];then
            cp -f src/xplhub/examples/config/xplhub.cfg $HUB_ETC/xplhub.cfg
            chown $d_user:root $HUB_ETC/xplhub.cfg
            chmod 640 $HUB_ETC/xplhub.cfg
        fi
    fi
    if [ -d "/etc/default/" ];then
        if [ "$keep" = "n" -o "$keep" = "N" ];then
            cp src/xplhub/examples/default/xplhub /etc/default/
        fi
    else
        echo "Can't find the directory where I can copy system-wide config. Usually it is /etc/default/"
        exit 6
    fi
    if [ -d "/etc/logrotate.d/" ];then
        cp src/xplhub/examples/logrotate/xplhub /etc/logrotate.d/
        chmod 644 /etc/logrotate.d/xplhub
    fi
}

function check_python {
    if [ ! -x "$(which python)" ];then
        echo "No python binary found, please install at least python2.6";
        exit 11
    else
        if python -V 2>&1|grep -qs "Python 2.[345]";then
            echo "Bad python version used, please install at least 2.6, and check /usr/bin/python starts the good version."
            exit 12
        fi
    fi
}

function create_log_dir {
    mkdir -p /var/log/xplhub
    chown -R $d_user: /var/log/xplhub 
}


function update_default_config {
    if [ ! -f /etc/default/xplhub ];then
        echo "Can't find /etc/default/xplhub!"
        exit 8
    fi
    [ -f /etc/default/xplhub ] &&  sed -i "s;^XPLHUB_USER.*$;XPLHUB_USER=$d_user;" /etc/default/xplhub
}


#Main part
echo "This install tool is linked to the new python xPL hub. This hub is not yet the official xPL hub for Domogik. Use it with caution"
echo "Press Enter to continue..."
read

if [ $UID -ne 0 ];then
    echo "Please restart this script as root!"
    exit 10
fi
if [ "$(dirname $0)" != "." ];then
    echo "Please run this script from main source directory (as ./install.sh"
    exit 15
fi

#stop_domogik
check_python
#test_sources $0
copy_sample_files
create_log_dir

# install netifaces and twisted
pip install twisted
pip install netifaces


echo "Everything seems to be good, the python xPL hub should be installed correctly."
trap - EXIT
