#!/bin/bash    

pkg_list="\
         build-essential \
         pkg-config \
         libzmq-dev \
         postgresql-common \
         libpq-dev \
         alembic \
         libzmq-dev \
         mysql-server \
         \
         python \
         python-setuptools \
         python-dev \
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

sudo aptitude install $pkg_list
sudo dpkg -l $pkg_list



echo << TXT "
to create data base:
mysql -p -u root
=============cut here=============
create database domogik;
grant usage on *.* to domogik@localhost identified by 'domopass';
grant all privileges on domogik.* to domogik@localhost ;
=============cut here============= 
"
TXT

