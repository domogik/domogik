#!/bin/bash -e 
# The -e option will make the bash stop if any command raise an error ($? != 0)

sudo apt-get update
sudo apt-get install libzmq3-dev
sudo pip install pyzmq
sudo pip install argparse
sudo apt-get install python2.7-dev gcc
sudo apt-get install libssl-dev
sudo apt-get install libmysqlclient-dev mysql-client
sudo pip install psycopg2
#sudo apt-get install python-versiontools
sudo pip install python-version-info

