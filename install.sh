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
#@copyright: (C) 2007-2009 Domogik project
#@license: GPL(v3)
#@organization: Domogik


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
                echo "Can't find setup.py, did you download the sources correctly ? "
                exit 1
            fi 
        ;;
        *)
            echo "Only modes develop and install are available"
        ;;
    esac
}

function test_sources {
    FILENAME=$1
    [ -d "$PWD/src" ] ||( echo "Can't find src/ directory, are you running this script from the sources main directory ? (with ./$FILENAME" && exit 2 )
    [ -f "src/domogik/examples/config/domogik.cfg" ] ||( echo "Can't find src/domogik/examples/config/domogik.cfg file !" && exit 3 )
    [ -f "src/domogik/examples/default/domogik" ] ||( echo "Can't find src/domogik/examples/default/domogik file !" && exit 4 )
    [ -f "src/domogik/examples/init/domogik" ] ||( echo "Can't find src/domogik/examples/init/domogik !" && exit 5 )
}

function copy_sample_files {
    if [ -d "/etc/default/" ];then
        cp src/domogik/examples/default/domogik /etc/default/
    else
        echo "Can't find the directory where I can copy system-wide config. Usually it is /etc/default/"
        exit 6
    fi
    if [ -d "/etc/init.d/" ];then
        cp src/domogik/examples/init/domogik /etc/init.d/ 
        chmod +x /etc/init.d/domogik
    elif [ -d "/etc/rc.d/" ];then
        cp src/domogik/examples/init/domogik /etc/rc.d/ 
        chmod +x /etc/rc.d/domogik
    else
        echo "Init directory does not exists (/etc/init.d or /etc/rc.d)"
        exit 7
    fi
}

function update_default_config {
    if [ ! -f /etc/default/domogik ];then
        echo "Can't find /etc/default/domogik !"
        exit 8
    fi
    read -p "Which user will run domogik, it will be created if it does not exist yet ? (default : domogik) " d_user
    d_user=${d_user:-domogik}
    if ! getent passwd $d_user >/dev/null;then
        echo "I can't find informations about this user !"
        read -p "Do you want to create it ? (y/n) " create
        if [ "$create" = "y" ];then
            adduser $d_user
        else
            echo "Please restart this script when the user $d_user will exists."
            exit 9
        fi
    fi
    [ -f /etc/default/domogik ] &&  sed -i "s;^DOMOGIK_USER.*$;DOMOGIK_USER=$d_user;" /etc/default/domogik

    d_home=$(getent passwd $d_user |cut -d ':' -f 6)

    if [ "$MODE" = "develop" ];then
        d_custom_path=$PWD/src/domogik/xpl/tools/
        [ -f /etc/default/domogik ] &&  sed -i "s;^CUSTOM_PATH.*$;CUSTOM_PATH=$d_custom_path;" /etc/default/domogik 
    fi
}

function update_user_config {
    if [ ! -f $d_home/.domogik.cfg ];then
        cp -f src/domogik/examples/config/domogik.cfg $d_home/.domogik.cfg
        chown $d_user: src/domogik/examples/config/domogik.cfg $d_home/.domogik.cfg
    fi
    if [ "$MODE" = "install" ];then
        prefix="/usr/local"
    else
        prefix=$PWD/src
    fi
    sed -i "s;^custom_prefix.*$;custom_prefix=$prefix;" $d_home/.domogik.cfg

    read -p "Which interface address do you want to bind to ? (default : 127.0.0.1) : " bind_addr
    bind_addr=${bind_addr:-127.0.0.1}
    sed -i "s/^bind_interface.*$/bind_interface = $bind_addr/" $d_home/.domogik.cfg
    sed -i "s/^rest_server_ip.*$/rest_server_ip = $bind_addr/" $d_home/.domogik.cfg
    sed -i "s/^django_server_ip.*$/django_server_ip = $bind_addr/" $d_home/.domogik.cfg
    sed -i "s/^django_rest_server_ip.*$/django_rest_server_ip = $bind_addr/" $d_home/.domogik.cfg
    echo "Info : Database will be created in $d_home/.domogik.sqlite"
    sed -i "s;^db_path.*$;db_path = $d_home/.domogik.sqlite;" $d_home/.domogik.cfg
}

function call_db_installer {
    su -c "$PWD/db_installer.py" $d_user
}

function check_python {
    if [ ! -x "/usr/bin/python" ];then
        echo "No python binary found, please install at least python2.6";
        exit 11
    else
        if python -V 2>&1|grep -qs "Python 2.[345]";then
            echo "Bad python version used, please install at least 2.6, and check /usr/bin/python starts the good version."
            exit 12
        fi
    fi
} 

function modify_hosts {
    if ! grep localhost /etc/hosts|grep -qs 127.0.0.1;then
        sed -i 's/^\(.*localhost.*\)$/#\1/' /etc/hosts 
        echo "127.0.0.1 localhost" >> /etc/hosts 
    fi
}

#Main part
if [ $UID -ne 0 ];then
    echo "Please restart this script as root !"
    exit 10
fi

check_python
test_sources $0
read -p "Which install mode do you want (choose develop if you don't know) ? [install/develop] : " MODE
while [ "$MODE" != "develop" -a "$MODE" != "install" ];do
    read -p "Which install mode do you want ? [install/develop] : " MODE
done
read -p "If you want to use a proxy, please set it now (ex: http://1.2.3.4:8080)" http_proxy
if [ "x$http_proxy" != "x" ];then
    export http_proxy
fi
run_setup_py $MODE
copy_sample_files 
update_default_config 
update_user_config 
call_db_installer 
modify_hosts

echo "Everything seems to be good, Domogik should be installed correctly."
echo "I will start the test_config.py script to check it."
read "Please press a key when ready."
chmod +x ./test_config.py && ./test_config.py
