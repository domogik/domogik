FROM debian:jessie
MAINTAINER Fritz SMH <fritz.smh@gmail.com>

### Configuration #################################

ENV domogik_release=develop
ENV domogikmq_release=1.4
ENV domoweb_release=develop

ENV ROOT_PASSWORD=domopass
ENV DOMOGIK_PASSWORD=domopass

###################################################
#
### How to...
#
# 1. Do development on git sources with the built image
# 
# TODO : explain
#
#
#
### TODO : 
#
# Improvments
# - process TODO in this Dockerfile
# - find a proper way to work on git sources and do the related doc (volumes)
#   - https://howchoo.com/g/zdq5m2exmze/docker-persistence-with-a-data-only-container
#   - https://howchoo.com/g/y2y1mtkznda/getting-started-with-docker-compose-and-django
#   - http://www.alexecollins.com/docker-persistence/
# - install weather
# - find a way with domoweb to put some widget automatically


### Apt 
RUN apt-get update 


### Tools not mandatory for Domogik but usefull for tests/debug/development

RUN apt-get install -y \
    vim  \
    telnet \
    wget \
    openssh-server \
    screen \
    dos2unix \
    tcpdump

### Minimum requirements
RUN apt-get install -y \
    sudo \
    python2.7-dev \
    python-pip \
    git 
    
RUN pip install netifaces \
 && pip install sphinx-better-theme

 
### Database server

# Install MySQL
# warning : no root password defined!
RUN DEBIAN_FRONTEND=noninteractive apt-get install -y mysql-server
# Create the empty database
RUN /bin/bash -c "/usr/bin/mysqld_safe &" \
 && sleep 5 \
 && mysql -u root -e "CREATE DATABASE domogik;" \
 && mysql -u root -e "GRANT ALL PRIVILEGES ON domogik.* to domogik@localhost IDENTIFIED BY 'domopass';"


### Create user and directories
RUN useradd -M domogik \
 && mkdir -p /opt/dmg \
 && chown domogik:domogik /opt/dmg

### Change passwords
RUN echo "root:$ROOT_PASSWORD" | chpasswd \
 && echo "domogik:$DOMOGIK_PASSWORD" | chpasswd

### Create a fake cron folder to avoid error during install
RUN mkdir -p /etc/cron.d/
 
 
### Deploy the sources

# 1. demo mode
# grab sources from a git tag
RUN cd /opt/dmg \
 && git clone https://github.com/domogik/domogik-mq.git \
 && cd /opt/dmg/domogik-mq \
 && git checkout ${domogikmq_release} 

RUN cd /opt/dmg \
 && git clone https://github.com/domogik/domogik.git \
 && cd /opt/dmg/domogik \
 && git checkout ${domogik_release}  

RUN cd /opt/dmg \
 && git clone https://github.com/domogik/domoweb.git \
 && cd /opt/dmg/domoweb \
 && git checkout ${domoweb_release}  



# 2. dev mode
# this is done from command line with -v
# TODO : improve...
#        currently this is only a copy
#COPY git/domogik /opt/dmg/domogik
#COPY git/domogik-mq /opt/dmg/domogik-mq

#RUN cd /opt/dmg/domogik-mq \
# && git checkout ${domogikmq_release} 

#RUN cd /opt/dmg/domogik \
# && git checkout ${domogik_release}  





### Install

# Patches. TODO : move before
RUN pip install Flask-Themes2
RUN apt-get install -y libpq-dev
RUN pip install alembic
RUN pip install SQLAlchemy-Utils

# Domogik-mq
RUN cd /opt/dmg/domogik-mq \
 && python install.py --daemon --user domogik --command-line 

# Domogik
# MySQL should be run before install !
RUN /bin/bash -c "/usr/bin/mysqld_safe &" \
 && sleep 5 \
 && cd /opt/dmg/domogik \
 && python install.py --user domogik --command-line --no-create-database --admin_interfaces "*" --admin_secret_key "dockersupersecretkey"

# Domoweb
RUN cd /opt/dmg/domoweb \
 && python install.py --user domogik 
 

### Install a few packages and their needed dependencies
RUN su - domogik -c "dmg_package -i http://github.com/fritz-smh/domogik-plugin-diskfree/archive/1.4.zip"
RUN su - domogik -c "dmg_package -i http://github.com/fritz-smh/domogik-plugin-weather/archive/1.4.zip"
RUN su - domogik -c "dmg_package -i http://github.com/domogik/domogik-brain-base/archive/1.3.zip"
RUN su - domogik -c "dmg_package -i http://github.com/fritz-smh/domogik-plugin-generic/archive/develop.zip"
RUN pip install npyscreen \
 && su - domogik -c "dmg_package -i http://github.com/fritz-smh/domogik-interface-chat/archive/develop.zip"


### Cleanup
RUN apt-get clean

### Expose ports
# 40404 : domoweb
# 40405 : domogik admin websocket
# 40406 : domogik admin http
# 3865 : xpl hub
EXPOSE 40404 40405 40406 22 3865


### Volumes
# we set /opt/dmg/ as a volume to allow changes to be kept from one run to another run in case of debugging tests.
VOLUME /opt/dmg/
# we set /var/log/domogik as a volume to allow checking logs from outside the container.
VOLUME /var/log/domogik/
# we set /var/lib/domogik as a volume to allow access to domogik packages and other components
VOLUME /var/lib/domogik/


### Startup actions
COPY scripts/startup.sh /opt/startup.sh
RUN chmod a+x /opt/startup.sh
CMD ["/bin/bash", "/opt/startup.sh"]


