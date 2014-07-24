#!/bin/bash -e 
# The -e option will make the bash stop if any command raise an error ($? != 0)
echo "PYTHONXXXX:"
ls -l $(which python)

OS=$(lsb_release -si)
ARCH=$(uname -m | sed 's/x86_//;s/i[3-6]86/32/')
VER=$(lsb_release -sr)

echo "OS  :$OS"
echo "ARCH:$ARCH"
echo "VER :$VER"

sudo apt-get update
sudo apt-get install libzmq3-dev
sudo pip install pyzmq
#sudo apt-get install python-argparse
sudo pip install argparse
sudo apt-get install python2.7-dev gcc
sudo apt-get install libssl-dev
sudo apt-get install libmysqlclient-dev mysql-client
#sudo apt-get install python-psycopg2
if [ "$OS" == "Debian" ];then
    sudo apt-get install python-mysqldb 
    sudo apt-get install Magic-file-extensions
else
    sudo pip install psycopg2
fi

