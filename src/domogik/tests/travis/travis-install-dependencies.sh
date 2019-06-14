#!/bin/bash -e 
# The -e option will make the bash stop if any command raise an error ($? != 0)
# repository for python3.6-dev
sudo add-apt-repository ppa:deadsnakes/ppa -y

sudo apt-get update
sudo apt-get install libzmq3-dev
pip3 install pyzmq
pip3 install argparse
sudo apt-get install python3.6-dev gcc
sudo apt-get install libssl-dev
sudo apt-get install libmysqlclient-dev #mysql-client
pip3 install psycopg2
pip3 install docutils
#pip3 install python-daemon==2.0.2
#pip3 install netifaces
sudo apt-get install python3-netifaces
pip3 install chardet

# for doc building
pip3 install sphinx
pip3 install sphinx-rtd-theme
pip3 install sphinxcontrib-actdiag
pip3 install sphinxcontrib-blockdiag
pip3 install sphinxcontrib-nwdiag
pip3 install sphinxcontrib-seqdiag

# get python version
export PYTHON_VER=`python --version | cut -c8-10`
