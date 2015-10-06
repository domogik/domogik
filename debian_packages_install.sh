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
         python-argparse \
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
apt-get install $pkg_list

pip_list="Flask-Login \
          Flask-Babel \
          Flask-Bootstrap \
          sphinx-better-theme \
         "

for elt in $pip_list
  do
    pip install $elt
done


