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
         libzmq3-dev \
         libpq-dev \
         libffi-dev \
         \
         python3 \
         python3-dev \
         python3-pkg-resources \
         python3-setuptools \
         python3-mysqldb \
         python3-sqlalchemy \
         python3-simplejson \
         python3-openssl \
         python3-psutil  \
         python3-mysqldb  \
         python3-psycopg2 \
         python3-pip \
         python3-serial \
         python3-netifaces \
         python3-twisted \
         python3-flask \
         python3-flaskext.wtf \
         python3-tornado \
         python3-requests \
         python3-magic \
         python3-zmq \
         python3-babel \
         python3-sphinx \
         libusb-1.0-0-dev \
         "
#         python-gluon \

apt-get update
continue $?

# special case for python argparse....
python3 -c "import argparse"
if [ $? -ne 0 ] ; then
    echo "Argparse module for python is not installed. Trying to install it..."
    pip3 install argparse
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
pip3 install -e git://github.com/sysr-q/flask-themes2.git#egg=flask_themes2-dev
continue $?

# standard packages
apt-get install $pkg_list
continue $?

pip_list="Flask-Login \
          Flask-Babel \
          Flask-Bootstrap \
          sphinx-better-theme \
          sqlalchemy-utils \
          linux-metrics \
          pytz \
          chardet
         "

for elt in $pip_list
  do
    pip3 install $elt
    continue $?
done


