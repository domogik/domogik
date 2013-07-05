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

MAIN_INSTALL=y
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


DMG_HOME=

DMG_ETC=/etc/domogik
DMG_CACHE=/var/cache/domogik
DMG_LIB=/var/lib/domogik
DMG_LOCK=/var/lock/domogik

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

function run_setup_py {
    MODE=$1
    case $MODE in
        develop|install)
            if [ -f "setup.py" ];then
                python ./ez_setup.py
                python ./setup.py $MODE
                if [ "x$?" != "x0" ];then
                    echo "setup.py script exists with a non 0 return value : $?"
                    exit 13
                fi
            else
                echo "Can't find setup.py, did you download the sources correctly? "
                exit 1
            fi
        ;;
        *)
            echo "Only develop and install modes are available"
        ;;
    esac
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

function call_app_installer {
    echo "** Calling Application Installer"
    /bin/su -c "python ./src/domogik/install/installer.py" $d_user
    if [ $? -ne 0 ];then
        echo "ERROR : An error occured during app_installer execution, read the previous lines for detail."
        exit 1
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

MODE=develop
stop_domogik
run_setup_py $MODE

read -p "If you want to use a proxy, please set it now. It will only be used during installation. (ex: http://1.2.3.4:8080)" http_proxy
if [ "x$http_proxy" != "x" ];then
    export http_proxy
fi
#this is needed now only because of old bug (#792) and should be useless for new install
if [ "$SUDO_USER" ];then
    trap "[ -d \"$HOME/.python-eggs\" ] && chown -R $SUDO_USER: $HOME/.python-eggs" EXIT
    [ -d "$HOME/.python-eggs" ] && chown -R $SUDO_USER: $HOME/.python-eggs/ 
else
    trap "[ -d \"$HOME/.python-eggs\" ] && chown -R $USER: $HOME/.python-eggs" EXIT
    [ -d "$HOME/.python-eggs" ] && chown -R $USER: $HOME/.python-eggs/ 
fi

create_domogik_user
python src/domogik/install/config.py -notest
call_app_installer
python src/domogik/install/test_config.py
