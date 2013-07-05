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
        --secondary) 
            MAIN_INSTALL="n"
            echo "This installation will be done as a secondary host installation : only manager (and plugins) will be launched on this host."
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

function copy_sample_files {
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

function update_default_config {
    if [ ! -f /etc/default/domogik ];then
        echo "Can't find /etc/default/domogik!"
        exit 8
    fi
    [ -f /etc/default/domogik ] &&  sed -i "s;^DOMOGIK_USER.*$;DOMOGIK_USER=$d_user;" /etc/default/domogik
    [ -f /etc/default/domogik ] &&  sed -i "s;^DOMOGIK_XPL_HUB.*$;DOMOGIK_XPL_HUB=${DOMOGIK_XPL_HUB};" /etc/default/domogik

    if [ "$MODE" = "develop" ];then
        arch_path=$(python src/domogik/install/get_arch.py)
        d_custom_path=$PWD/$arch_path
        [ -f /etc/default/domogik ] &&  sed -i "s;^CUSTOM_PATH.*$;CUSTOM_PATH=$d_custom_path;" /etc/default/domogik
    fi
}

function update_default_config_other_hosts {
    if [ ! -f /etc/default/domogik ];then
        echo "Can't find /etc/default/domogik!"
        exit 8
    fi
    [ -f /etc/default/domogik ] &&  sed -i "s;^MANAGER_PARAMS.*$;MANAGER_PARAMS=\"-p\";" /etc/default/domogik
}

function update_user_config {
            
    if [ "$keep" = "n" -o "$keep" = "N" ];then
        if [ "$MODE" = "install" ];then
            prefix=""
            sed -i "s;^package_path.*$;package_path = $DMG_LIB;" $DMG_ETC/domogik.cfg
            sed -i "s;^#src_prefix.*$;#src_prefix = $prefix;" $DMG_ETC/domogik.cfg
        else
            prefix=$PWD/src
            sed -i "s;^package_path.*$;#package_path = $DMG_LIB;" $DMG_ETC/domogik.cfg
            sed -i "s;^#src_prefix.*$;src_prefix = $prefix;" $DMG_ETC/domogik.cfg
        fi

        read -p "Which interface do you want to bind to? (default : lo) : " bind_iface
        bind_iface=${bind_iface:-lo}
        bind_addr=$($CMD_NET $bind_iface|egrep -o "[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}"|head -1)
        if [ "x$bind_addr" = "x" ];then
            echo "Can't find the address associated to the interface!"
            exit 20
        fi
        sed -i "s/^bind_interface.*$/bind_interface = $bind_addr/" $DMG_ETC/domogik.cfg
        sed -i "s/^HUB_IFACE.*$/HUB_IFACE=$bind_iface/" /etc/default/domogik
        # will be overide on secondary host
        sed -i "s/^rest_server_ip.*$/rest_server_ip = $bind_addr/" $DMG_ETC/domogik.cfg
        sed -i "s/^ip.*$/ip = $bind_addr/" $DMG_ETC/domogik.cfg
    fi
}

function update_rest_config_for_secondary_host {
    if [ "$keep" = "n" -o "$keep" = "N" ];then
        read -p "Ip of the main Domogik installation (ip of Rest server) : " rest_server_ip
        read -p "Port of the main Domogik installation (port of Rest server) : " rest_server_port
        sed -i "s/^rest_server_ip.*$/rest_server_ip = $rest_server_ip/" $DMG_ETC/domogik.cfg
        sed -i "s/^rest_server_port.*$/rest_server_port = $rest_server_port/" $DMG_ETC/domogik.cfg
    fi
}


function update_user_config_db {
           
    # if keep == n
    #  => select the db type (mysql or postgresql
    #  => display auth depenting on the DB type
    # db_ok = false
    # if keep === y
    #  => test the connection based on the config
    #  => set db_ok to result
    # while db_ok == false
    #  => request info comman to all dbs
    #  => test the connection based on the config
    #  => set db_ok to result
    # write out to the file
 
    if [ "$keep" = "n" -o "$keep" = "N" ];then
        # request what db to use
        read -p "Db Type (mysql or postgresql) [mysql] :" db_type
        if [ "$db_type" = "" ];then 
	    db_type="mysql"
        fi
        #Display config config
        if [ "$db_type" = "mysql" ];then 
            echo "You need to have a working Mysql server with a domogik user and database."
            echo "You can create it using these commands (as mysql admin user) :"
            echo " > CREATE DATABASE domogik;"
            echo " > GRANT ALL PRIVILEGES ON domogik.* to domogik@127.0.0.1 IDENTIFIED BY 'randompassword';"
        else
            echo "You need to have a working Postgresql server with a domogik user and database."
            echo "You can create it using these commands (as postgresql admin user) :"
            echo " > su - postgres"
            echo " > createdb domogik"
            echo " > createuser --no-createdb --no-adduser --no-createrole -P domogik"
            echo " > exit"
        fi
        read -p "Press Enter to continue the installation when your setup is ok. "
    fi
    db_ok=

    if [ "$keep" = "y" -o "$keep" = "Y" ];then
        db_user=$(grep "^db_user" $DMG_ETC/domogik.cfg|cut -d'=' -f2|tr -d ' ')
        db_type=$(grep "^db_type" $DMG_ETC/domogik.cfg|cut -d'=' -f2|tr -d ' ')
        db_password=$(grep "^db_password" $DMG_ETC/domogik.cfg|cut -d'=' -f2|tr -d ' ')
        db_port=$(grep "^db_port" $DMG_ETC/domogik.cfg|cut -d'=' -f2|tr -d ' ')
        db_name=$(grep "^db_name" $DMG_ETC/domogik.cfg|cut -d'=' -f2|tr -d ' ')
        db_host=$(grep "^db_host" $DMG_ETC/domogik.cfg|cut -d'=' -f2|tr -d ' ')
        if [ "$db_type" = "mysql" ];then
            echo "SELECT 1;"|mysql -h$db_host -P$db_port -u$db_user -p$db_password $db_name > /dev/null
        else
            psql -h $db_host -p $db_port -U $db_user -d $db_name -c "SELECT 1;" > /dev/null
        fi
        if [ $? -ne 0 ];then
            read -p "Something was wrong, can't access to the database, please check your setup and press Enter to retry."
        else
            db_ok=true
        fi
    fi
    while [ ! $db_ok ];do 
        echo "Please set your database parameters."
        read -p "Username : " db_user
        stty -echo echonl
        read -p "Password : " db_password
        stty echo
        if [ "$db_type" = "mysql" ];then
            read -p "Port [3306] : " db_port
            if [ "$db_port" = "" ];then 
                db_port=3306 
            fi
        else
            read -p "Port [5432] : " db_port
            if [ "$db_port" = "" ];then 
                db_port=5432 
            fi
        fi
        read -p "Host [127.0.0.1] :" db_host
        if [ "$db_host" = "" ];then 
            db_host="127.0.0.1"
        fi
        read -p "Database name [domogik]: " db_name
        if [ "$db_name" = "" ];then 
            db_name="domogik"
        fi
        if [ "$db_type" = "mysql" ];then
            echo "SELECT 1;"|mysql -h$db_host -P$db_port -u$db_user -p$db_password $db_name > /dev/null
        else 
            psql -h $db_host -p $db_port -U $db_user -d $db_name -c "SELECT 1;" > /dev/null
        fi
        if [ $? -ne 0 ];then
            read -p "Something was wrong, can't access to the database, please check your setup and press Enter to retry."
        else
            db_ok=true
            echo "Connection test OK"
            sed -i "s;^db_type.*$;db_type = $db_type;" $DMG_ETC/domogik.cfg
            sed -i "s;^db_user.*$;db_user = $db_user;" $DMG_ETC/domogik.cfg
            sed -i "s;^db_password.*$;db_password = $db_password;" $DMG_ETC/domogik.cfg
            sed -i "s;^db_port.*$;db_port = $db_port;" $DMG_ETC/domogik.cfg
            sed -i "s;^db_name.*$;db_name = $db_name;" $DMG_ETC/domogik.cfg
            sed -i "s;^db_host.*$;db_host = $db_host;" $DMG_ETC/domogik.cfg
        fi
    done
}

function call_app_installer {
    echo "** Calling Application Installer"
    /bin/su -c "python ./src/domogik/install/installer.py" $d_user
    if [ $? -ne 0 ];then
        echo "ERROR : An error occured during app_installer execution, read the previous lines for detail."
        exit 1
    fi
}

function modify_hosts {
    [ -f "/etc/hosts" ] || touch /etc/hosts
    if ! grep localhost /etc/hosts|grep -qs 127.0.0.1;then
        sed -i 's/^\(.*localhost.*\)$/#\1/' /etc/hosts
        echo "127.0.0.1 localhost" >> /etc/hosts
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
keep=n
CMD_NET='ip addr show'
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

run_setup_py $MODE
copy_sample_files
update_default_config
if [ $MAIN_INSTALL = "n" ] ; then
    update_default_config_other_hosts
fi
update_user_config
if [ $MAIN_INSTALL = "y" ] ; then
    update_user_config_db
else
    update_rest_config_for_secondary_host
fi
#create_log_dir
if [ $MAIN_INSTALL = "y" ] ; then
    call_app_installer
    #install_plugins
fi
modify_hosts   


echo "Everything seems to be good, Domogik should be installed correctly."
echo "I will start the test_config.py script to check it."
read -p "Please press Enter when ready."
chmod +x ./src/domogik/install/test_config.py && ./src/domogik/install/test_config.py
if [ "$SUDO_USER" ];then
    [ -d "$HOME/.python-eggs" ] && chown -R $SUDO_USER: $HOME/.python-eggs/ 
else
    [ -d "$HOME/.python-eggs" ] && chown -R $USER: $HOME/.python-eggs/ 
fi
trap - EXIT
