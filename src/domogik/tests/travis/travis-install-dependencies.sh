#!/bin/bash -e 
# The -e option will make the bash stop if any command raise an error ($? != 0)

sudo apt-get update
sudo apt-get install libzmq3-dev
pip install pyzmq
pip install argparse
sudo apt-get install python2.7-dev gcc
sudo apt-get install libssl-dev
sudo apt-get install libmysqlclient-dev mysql-client
sudo pip install psycopg2
#sudo apt-get install python-versiontools
#sudo pip install python-version-info
sudo pip install docutils
sudo pip uninstall python-daemon
#rm /usr/lib/python2.7/dist-packages/easy_install.pyc
sudo pip install python-daemon==2.0.2 ## see http://stackoverflow.com/questions/27972349/installing-latest-python-daemon-2-0-3-breaks-subsequent-pip-installs

