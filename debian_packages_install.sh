#!/bin/bash 

# INFORMATIONS
# ============
#
# * mysql-server is not installed by the install.py script as the database must 
#   be created before launching the install.py script


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
         python-flask-login \
         python-flask-babel \
         python-gluon \
         python-babel \
         "

sudo apt-get update
sudo apt-get install $pkg_list


