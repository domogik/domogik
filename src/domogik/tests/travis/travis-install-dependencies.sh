#!/bin/bash -e 
# The -e option will make the bash stop if any command raise an error ($? != 0)

sudo apt-get update
sudo apt-get install libzmq3-dev
pip install pyzmq
pip install argparse
sudo apt-get install python2.7-dev gcc
sudo apt-get install libssl-dev
sudo apt-get install libmysqlclient-dev #mysql-client
pip install psycopg2
pip install docutils
#pip install python-daemon==2.0.2
#pip install netifaces
sudo apt-get install python-netifaces
pip install chardet

# for doc building
pip install sphinx
pip install sphinx-rtd-theme
pip install sphinxcontrib-actdiag
pip install sphinxcontrib-blockdiag
pip install sphinxcontrib-nwdiag
pip install sphinxcontrib-seqdiag
