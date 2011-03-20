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
                echo "Can't find setup.py, did you download the sources correctly? "
                exit 1
            fi
        ;;
        *)
            echo "Only develop and install modes are available"
        ;;
    esac
}

function test_sources {
    FILENAME=$1
    [ -d "$PWD/src" ] ||( echo "Can't find src/ directory, are you running this script from the sources main directory? (with ./$FILENAME" && exit 2 )
    [ -f "src/domogik/examples/config/domogik.cfg" ] ||( echo "Can't find src/domogik/examples/config/domogik.cfg file!" && exit 3 )
    [ -f "src/domogik/examples/default/domogik" ] ||( echo "Can't find src/domogik/examples/default/domogik file!" && exit 4 )
    [ -f "src/domogik/examples/init/domogik" ] ||( echo "Can't find src/domogik/examples/init/domogik!" && exit 5 )
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
    d_home=$(getent passwd $d_user |cut -d ':' -f 6)
    keep="n"
    already_cfg=
    if [ ! -f $d_home/.domogik.cfg ];then
        cp -f src/domogik/examples/config/domogik.cfg $d_home/.domogik.cfg
        chown $d_user: src/domogik/examples/config/domogik.cfg $d_home/.domogik.cfg
    else
        keep="y"
        already_cfg=1
        read -p "You already have a .domogik.cfg file. Do you want to keep it ? [Y/n]" keep
        if [ "x$keep" = "x" ];then
            keep="y"
        fi
        if [ "$keep" = "n" -o "$keep" = "N" ];then
            cp -f src/domogik/examples/config/domogik.cfg $d_home/.domogik.cfg
            chown $d_user: src/domogik/examples/config/domogik.cfg $d_home/.domogik.cfg
        fi
    fi
    if [ -d "/etc/default/" ];then
        if [ "$keep" = "n" -o "$keep" = "N" ];then
            cp src/domogik/examples/default/domogik /etc/default/
        fi
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
        echo "Init directory does not exist (/etc/init.d or /etc/rc.d)"
        exit 7
    fi
}

function update_default_config {
    if [ ! -f /etc/default/domogik ];then
        echo "Can't find /etc/default/domogik!"
        exit 8
    fi
    [ -f /etc/default/domogik ] &&  sed -i "s;^DOMOGIK_USER.*$;DOMOGIK_USER=$d_user;" /etc/default/domogik


    #[ -f $d_home/.domogik.cfg ] && rm -f $d_home/.domogik.cfg

    if [ "$MODE" = "develop" ];then
        arch=$(python -c 'import platform;print platform.architecture()[0]')
        d_custom_path=$PWD/src/domogik/xpl/tools/$arch/
        [ -f /etc/default/domogik ] &&  sed -i "s;^CUSTOM_PATH.*$;CUSTOM_PATH=$d_custom_path;" /etc/default/domogik
    fi
}

function update_user_config {
            
    if [ "$keep" = "n" -o "$keep" = "N" ];then
        if [ "$MODE" = "install" ];then
            prefix="/usr/local"
        else
            prefix=$PWD/src
        fi
        sed -i "s;^custom_prefix.*$;custom_prefix=$prefix;" $d_home/.domogik.cfg

        read -p "Which interface do you want to bind to? (default : lo) : " bind_iface
        bind_iface=${bind_iface:-lo}
        bind_addr=$(ifconfig $bind_iface|egrep -o "[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}"|head -1)
        if [ "x$bind_addr" = "x" ];then
            echo "Can't find the address associated to the interface!"
            exit 20
        fi
        sed -i "s/^bind_interface.*$/bind_interface = $bind_addr/" $d_home/.domogik.cfg
        sed -i "s/^HUB_IFACE.*$/HUB_IFACE=$bind_iface/" /etc/default/domogik
        sed -i "s/^rest_server_ip.*$/rest_server_ip = $bind_addr/" $d_home/.domogik.cfg
        sed -i "s/^django_server_ip.*$/django_server_ip = $bind_addr/" $d_home/.domogik.cfg
        sed -i "s/^internal_rest_server_ip.*$/internal_rest_server_ip = $bind_addr/" $d_home/.domogik.cfg
        read -p "If you need to reach Domogik from outside, you can specify an IP now : " out_bind_addr
        sed -i "s/^external_rest_server_ip.*$/external_rest_server_ip = $out_bind_addr/" $d_home/.domogik.cfg
        
        #Mysql config 
        echo "You need to have a working Mysql server with a domogik user and database."
        echo "You can create it using these commands (as mysql admin user) :"
        echo " > CREATE DATABASE domogik;"
        echo " > GRANT ALL PRIVILEGES ON domogik.* to domogik@localhost IDENTIFIED BY 'randompassword';"
        read -p "Press Enter to continue the installation when your setup is ok. "
    fi
    upgrade_sql="n"
    if [ $already_cfg ];then
        read -p "Do you want to upgrade your SQL database ? [y/N]" upgrade_sql
    else
        upgrade_sql="y"
    fi

    if [ "$keep" = "y" -o "$keep" = "Y" ];then
        db_user=$(grep "^db_user" $d_home/.domogik.cfg|cut -d'=' -f2|tr -d ' ')
        db_type=$(grep "^db_type" $d_home/.domogik.cfg|cut -d'=' -f2|tr -d ' ')
        db_password=$(grep "^db_password" $d_home/.domogik.cfg|cut -d'=' -f2|tr -d ' ')
        db_port=$(grep "^db_port" $d_home/.domogik.cfg|cut -d'=' -f2|tr -d ' ')
        db_name=$(grep "^db_name" $d_home/.domogik.cfg|cut -d'=' -f2|tr -d ' ')
        db_host=$(grep "^db_host" $d_home/.domogik.cfg|cut -d'=' -f2|tr -d ' ')
        mysql_client=$(which mysql)
        while [ ! -f "$mysql_client" ];do
            read -p "Mysql client not installed, please install it and press Enter."
            mysql_client=$(which mysql)
        done
        echo "SELECT 1;"|mysql -h$db_host -P$db_port -u$db_user -p$db_password $db_name > /dev/null
        if [ $? -ne 0 ];then
            read -p "Something was wrong, can't access to the database, please check your setup and press Enter to retry."
        else
            mysql_ok=true
        fi
    fi
    mysql_ok=
    while [ ! $mysql_ok ];do 
        echo "Please set your mysql parameters."
        read -p "Username : " db_user
        read -p "Password : " db_password
        read -p "Port [3306] : " db_port
        if [ "$db_port" = "" ];then 
            db_port=3306 
        fi
        read -p "Host [localhost] :" db_host
        if [ "$db_host" = "" ];then 
            db_host="localhost"
        fi
        read -p "Database name [domogik]: " db_name
        if [ "$db_name" = "" ];then 
            db_name="domogik"
        fi
        mysql_client=$(which mysql)
        while [ ! -f "$mysql_client" ];do
            read -p "Mysql client not installed, please install it and press Enter."
            mysql_client=$(which mysql)
        done
        echo "SELECT 1;"|mysql -h$db_host -P$db_port -u$db_user -p$db_password $db_name > /dev/null
        if [ $? -ne 0 ];then
            read -p "Something was wrong, can't access to the database, please check your setup and press Enter to retry."
        else
            mysql_ok=true
            echo "Connection test OK"
            sed -i "s;^db_type.*$;db_type = mysql;" $d_home/.domogik.cfg
            sed -i "s;^db_user.*$;db_user = $db_user;" $d_home/.domogik.cfg
            sed -i "s;^db_password.*$;db_password = $db_password;" $d_home/.domogik.cfg
            sed -i "s;^db_port.*$;db_port = $db_port;" $d_home/.domogik.cfg
            sed -i "s;^db_name.*$;db_name = $db_name;" $d_home/.domogik.cfg
            sed -i "s;^db_host.*$;db_host = $db_host;" $d_home/.domogik.cfg
            if [ "$upgrade_sql" = "n" -o "$upgrade_sql" = "N" ];then
                    return
            fi
        fi
        nb_tables=$(echo "SHOW TABLES;"|mysql -h$db_host -P$db_port -u$db_user -p$db_password $db_name |grep -vc ^Tables)
        if [ $nb_tables -ne 0 ];then
            read -p "Your database already contains some tables, do you want to drop them. If you choose No, new items will *NOT* be installed ? [Y/n]" drop_db
            if [ "$drop_db" = "" -o "$drop_db" = "y" -o "$drop_db" = "Y" ];then
                echo "SHOW TABLES;"|mysql -h$db_host -P$db_port -u$db_user -p$db_password $db_name |grep -v ^Tables|while read table;do
                    echo "DROP TABLE $table;"|mysql -h$db_host -P$db_port -u$db_user -p$db_password $db_name > /dev/null
                done
            fi
        fi
    done
}

function call_db_installer {
    if [ "$upgrade_sql" = "y" -o "$upgrade_sql" = "Y" ];then
        if [ "$drop_db" = "y" -o "$drop_db" = "Y" -o "$drop_db" = "" ];then 
            echo "** Call DB Installer"
            /bin/su -c "python ./db_installer.py" $d_user
            if [ $? -ne 0 ];then
                echo "ERROR : An error occured during db_installer execution, read the previous lines for detail."
                exit 1
            fi
        fi
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

function copy_tools {
    [ -d "/usr/local/bin" ] && (cp -f src/tools/dmg* /usr/local/bin;chmod +x /usr/local/bin/dmg*)
}

function modify_hosts {
    [ -f "/etc/hosts" ] || touch /etc/hosts
    if ! grep localhost /etc/hosts|grep -qs 127.0.0.1;then
        sed -i 's/^\(.*localhost.*\)$/#\1/' /etc/hosts
        echo "127.0.0.1 localhost" >> /etc/hosts
    fi
}

function create_log_dir {
    mkdir -p /var/log/domogik
    chown $d_user: /var/log/domogik 
}

function install_plugins {
    chmod +x src/tools/packages/insert_data.py 
    for file in src/share/domogik/plugins/*.xml;do
        echo "** Parse $file"
        su -c "src/tools/packages/insert_data.py $file" $d_user
        echo "** File $file parsed"
    done
    for file in src/share/domogik/hardwares/*.xml;do
        echo "** Parse $file"
        su -c "src/tools/packages/insert_data.py $file" $d_user
        echo "** File $file parsed"
    done
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

check_python
test_sources $0
read -p "Which install mode do you want (choose develop if you don't know)? [install/develop] : " MODE
while [ "$MODE" != "develop" -a "$MODE" != "install" ];do
    read -p "Which install mode do you want? [install/develop] : " MODE
done
read -p "If you want to use a proxy, please set it now. It will only be used during installation. (ex: http://1.2.3.4:8080)" http_proxy
if [ "x$http_proxy" != "x" ];then
    export http_proxy
fi
trap "[ -d "$HOME/.python-eggs" ] && chown -R $USER: $HOME/.python-eggs" EXIT

run_setup_py $MODE
copy_sample_files
update_default_config
update_user_config
copy_tools
create_log_dir
call_db_installer
install_plugins
modify_hosts

[ -d $HOME/.python-eggs ] && chown -R $USER: $HOME/.python-eggs/ 

echo "Everything seems to be good, Domogik should be installed correctly."
echo "I will start the test_config.py script to check it."
read -p "Please press Enter when ready."
chmod +x ./test_config.py && ./test_config.py
