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


