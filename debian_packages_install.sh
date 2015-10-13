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
python -c "import argparse"
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

# special case for Flask-theme2
# Some Ubuntu 14.04 and 15.04 users encountered this error during the installation :
# Searching for Flask-Themes2
# Reading https://pypi.python.org/simple/Flask-Themes2/
# Best match: Flask-Themes2 0.1.4.linux-x86-64
# Downloading https://pypi.python.org/packages/any/F/Flask-Themes2/Flask-Themes2-0.1.4.linux-x86_64.tar.gz#md5=71321801f51576557850b4b08b70af89
# Processing Flask-Themes2-0.1.4.linux-x86_64.tar.gz
# error: Couldn't find a setup script in /tmp/easy_install-KnIzW3/Flask-Themes2-0.1.4.linux-x86_64.tar.gz
# ========= TRACEBACK =============
# Traceback (most recent call last):
#   File "./install.py", line 427, in install
#     raise OSError("setup.py doesn't finish correctly")
# OSError: setup.py doesn't finish correctly
# 
# =================================
# ERROR:root:(<type 'exceptions.OSError'>, OSError("setup.py doesn't finish correctly",), <traceback object at 0x7f53e6139200>)
#  ==> (<type 'exceptions.OSError'>, OSError("setup.py doesn't finish correctly",), <traceback object at 0x7f53e6139200>)
pip install -e git://github.com/sysr-q/flask-themes2.git#egg=flask_themes2-dev
continue $? 

# standard packages
apt-get install $pkg_list
continue $? 

pip_list="Flask-Login \
          Flask-Babel \
          Flask-Bootstrap \
          sphinx-better-theme \
          sqlalchemy-utils \
         "

for elt in $pip_list
  do
    pip install $elt
    continue $? 
done


