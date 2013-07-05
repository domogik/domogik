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
#Help to manage Domogik installation
#
#Implements
#==========
#
#
#@author: Maxence Dunnewind <maxence@dunnewind.net>
#@copyright: (C) 2007-2012 Domogik project
#@license: GPL(v3)
#@organization: Domogik

# Manage options
function display_usage {
    echo "Usage : "
    echo "  Full installation : ./install.sh"
    echo "  Installation on secondary host : ./install.sh --secondary"
    echo "  Use the C xPL hub instead of the python one : ./install.sh --hub_c"
    echo "  Help : ./install.sh -h"
    echo "         ./install.sh --help"
}

DOMOGIK_XPL_HUB=python
while [ "$1" ] ; do 
    arg=$1
    case $arg in
        --hub_c) 
            DOMOGIK_XPL_HUB="c"
            echo "The C version of the xPL hub will be used instead of the python one."
            ;;
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

function stop_domogik {
    if [ -f "/etc/init.d/domogik" -o -f "/etc/rc.d/domogik" ];then
        if [ -d "/var/run/domogik" ];then
            [ -f /etc/conf.d/domogik ] && . /etc/conf.d/domogik
            [ -f /etc/default/domogik ] && . /etc/default/domogik
            if [ -f "/etc/domogik/domogik.cfg" ];then
                echo "There is already a Domogik on this system. Try to stop it before installation..."
                /etc/init.d/domogik stop
            fi
        fi
    fi
}

function create_domogik_user {
    read -p "Which user will run domogik, it will be created if it does not exist yet? (default : domogik) " d_user
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
}

#Main part
if [ $UID -ne 0 ];then
    echo "Please restart this script as root!"
    exit 10
fi
if [ "$(dirname $0)" != "." ];then
    echo "Please run this script from main source directory (as ./install.sh"
    exit 15
fi
if [ "$(pwd | cut -d"/" -f2)" == "root" ];then
    echo "Please use the Domogik package outside of the /root/ folder"
    exit 20
fi

stop_domogik
python ez_setup.py
python setup.py develop
if [ "x$?" != "x0" ];then
    echo "setup.py script exists with a non 0 return value : $?"
    exit 13
fi

read -p "If you want to use a proxy, please set it now. It will only be used during installation. (ex: http://1.2.3.4:8080)" http_proxy
if [ "x$http_proxy" != "x" ];then
    export http_proxy
fi
create_domogik_user
python src/domogik/install/config.py -notest
python src/domogik/install/installer.py $d_user
python src/domogik/install/test_config.py
