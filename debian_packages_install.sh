#!/bin/bash 

# INFORMATIONS
# ============
#
# * mysql-server is not installed by the install.py script as the database must 
#   be created before launching the install.py script

# Make sure only root can run our script
if [ "$(id -u)" != "0" ]; then
    echo "This script must be run as root" 1>&2
    exit 1
fi


function continue() {

    if [ $1 -ne 0 ] ; then
        echo "Something bad happens during command"
        echo "You should stop this step to see what is bad"
        cont=""
        while [ "x${cont}" == "x" ] ; do
            echo "Continue [Y/n] ?"
            read cont
            if [ "x${cont}" == "xY" ] ; then
                echo "OK, let's continue..."
            elif [ "x${cont}" == "xn" ] ; then
                echo "Exiting!"
                exit 1
            else
                cont=""
            fi
        done
    fi
}

pkg_list="\
         git \
         alembic \
         gettext \
         gcc\
         libssl-dev \
         libzmq-dev \
         libpq-dev \
         libffi-dev \
         \
         python \
         python-dev \
         python-pkg-resources \
         python-setuptools \
         python-mysqldb \
         python-sqlalchemy \
         python-simplejson \
         python-openssl \
         python-psutil  \
         python-mysqldb  \
         python-psycopg2 \
         python-pip \
         python-serial \
         python-netifaces \
         python-twisted \
         python-flask \
         python-flaskext.wtf \
         python-tornado \
         python-requests \
         python-daemon \
         python-magic \
         python-zmq \
         python-gluon \
         python-babel \
         python-sphinx \
         libusb-1.0-0-dev \
         "

apt-get update
continue $? 
    
# special case for python argparse....
python -c "import argparsex"
if [ $? -ne 0 ] ; then
    echo "Argparse module for python is not installed. Trying to install it..."
    pip install argparse
    if [ $? -ne 0 ] ; then
        echo "Error while installing argparse module"
        continue $? 
    fi

else
    echo "Argparse module for python is already installed"
fi

# standard packages
apt-get install $pkg_list
continue $? 

pip_list="Flask-Login \
          Flask-Babel \
          Flask-Bootstrap \
          sphinx-better-theme \
         "

for elt in $pip_list
  do
    pip install $elt
    continue $? 
done


