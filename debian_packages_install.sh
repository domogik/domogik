#!/bin/bash 

pkg_list="\
         alembic \
         mysql-server \
         gettext \
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

sudo apt-get install $pkg_list

echo to create data base enter Root password:
mysql -p -u root << TXT 
create database domogik;
grant usage on *.* to domogik@localhost identified by 'domopass';
grant all privileges on domogik.* to domogik@localhost ;
quit
TXT
if [ "$?" != 0 ];then
    echo "database already present ?"
fi

