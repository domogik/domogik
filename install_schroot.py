#!/usr/bin/python
# coding=UTF-8


#
# $Author : $
# $Date : $
# $Rev : $
#

import os
import sys
import tarfile
import logging 
from subprocess import check_call,call,CalledProcessError
import stat
import ConfigParser
import socket
import time
import ConfigParser

debian_version="wheezy"
#by default current user
#schroot_user="pnb"
domogik_git="/home/pnb/_git/domogik/domogik"
domogik_chroot="/srv/chroot/domogik"
domogik_chroot_git=domogik_chroot+"/root/domogik "
domogik_chroot_clean="/srv/chroot/domogik_clean"

aptitude_pkg = "\
                python \
                python-setuptools \
                build-essential \
                python-dev \
                pkg-config \
                libzmq-dev \
                postgresql-common \
                libpq-dev \
                python-mysqldb \
                python-argparse \
                python-sqlalchemy \
                alembic \
                python-simplejson \
                python-openssl \
                python-psutil  \
                python-mysqldb  \
                python-psycopg2 \
                python-serial \
                python-netifaces \
                python-twisted \
                python-flask \
                python-flaskext.wtf \
                python-tornado \
                python-requests \
                python-daemon \
                python-magic \
                "
#   too old but will try with it 
aptitude_pkg += "\
                python-zmq \
                libzmq-dev \
                "
#   for debian jessie (testing) only
aptitude_pkg += "\
                 python-flask-login \
                 python-flask-babel \
                 "
# not needed in chroot use host mysql
#                 mysql-server \

#python-pip \


#password
RSYNC_OPTION=" -ahvz --delete-after "

def print_step(str):
    log.info("")
    log.info('*'*80)
    for l in str.split('\n'):
        log.info('* '+l+' '*(80-2-2-len(l))+' *')
    log.info('*'*80)
    log.info("")
    

def print_comment(str):
    log.info("")
    log.info('* '+str+' '+'*'*(80-2-2-len(str))+'*')
    log.info("")

def print_cut_here(str):
    log.info("-------------cut_here--------------")
    log.info(str)
    log.info("-------------cut_here--------------")

def shell(cmd):
    log.info("*******"+cmd+"******")
    return call(cmd,shell=True)

def shell_in_chroot(chroot,cmd="",directory="/root"):
    log.info("******* in "+chroot+" do "+cmd+"******")

    cmd_line = ("sudo schroot -c %s --directory %s %s "%(
                                                         chroot,
                                                         directory,
                                                         cmd
                                                        )
               )
    return call(cmd_line,shell=True)

def install():
    print_step("Aptiude install ")


    print_step("sudo aptitude start...")
    check_call("sudo aptitude install debootstrap schroot",shell=True)

    if not os.path.exists(domogik_chroot_clean):
        print_step("Create debootstrap start...")
        check_call("sudo debootstrap "+debian_version+" "+domogik_chroot_clean,shell=True)

    f = open("/tmp/domogik_chroot.conf","w")
    f.write("[domogik-%s]\n"% debian_version )
    f.write("description=Debian %s (stable) 32-bit\n" % debian_version)
    f.write("directory=%s\n" % domogik_chroot)
    f.write("users=%s\n"%schroot_user)
    f.write("groups=sbuild-security\n")
    f.write("aliases=domogik\n")
    f.write("personality=linux32\n")
    f.write("\n")
    f.write("[domogik-clean-%s]\n"% debian_version )
    f.write("description=Debian %s (stable) 32-bit\n" % debian_version)
    f.write("directory=%s\n" % domogik_chroot_clean)
    f.write("users=%s\n"%schroot_user)
    f.write("groups=sbuild-security\n")
    f.write("aliases=domogik_clean\n")
    f.write("personality=linux32\n")
    f.write("\n")
    f.close()

    if not os.path.exists(domogik_chroot_clean):
        check_call("sudo mkdir /etc/schroot/chroot.d/ ",shell=True)
    check_call("sudo cp /tmp/domogik_chroot.conf /etc/schroot/chroot.d/ ",shell=True)

    shell_in_chroot("domogik_clean","aptitude install \
                    apt-show-versions " +
                    aptitude_pkg 
                    )

    shell_in_chroot("domogik_clean","apt-show-versions " +
                    aptitude_pkg 
                    )




    clean_chroot()
    chroot_intall()

def chroot_intall():
    shell_in_chroot("domogik","./install.py","/root/domogik/domogik")


"""

#not in debian :(
#python-Distutils2 \

#libzmq
aptitude install autotools-dev git libtool autoconf automake 
git clone git://github.com/zeromq/libzmq.git
./autogen.sh
./configure.sh
make
make install

domogik/examples/default/domogik => /etc/default/
mkdir /etc/domogik
cp domogik/examples/config/domogik.cfg.sample /etc/domogik/domogik.cfg
mkdir /var/log/domogik
mkdir /var/run/domogik
"""

def clean_chroot():
    shell("sudo rsync --exclude=proc "+RSYNC_OPTION+" "+domogik_chroot_clean+"/* "+domogik_chroot+" ")
    if not os.path.exists(domogik_chroot_git):
        check_call("sudo mkdir "+domogik_chroot_git,shell=True)
    shell("sudo rsync "+RSYNC_OPTION+" "+domogik_git+" "+domogik_chroot_git)
    shell("sudo mkdir "+domogik_git+"/proc")
    shell("sudo mount -o bind /proc/ "+domogik_git+"/proc")

if __name__ == '__main__' :

    FORMAT = "%(asctime)-15s %(clientip)s %(user)-8s %(message)s"
    logging.basicConfig(format=FORMAT)
    log = logging

    if not 'schroot_user' in globals():
        schroot_user = os.environ['USER']
        log.info("use %s"%schroot_user)

    if 'db' in sys.argv:
        print """
create database domogik;
grant usage on *.* to domogik@localhost identified by 'domopass';
grant all privileges on domogik.* to domogik@localhost ;
        """

    if 'install' in sys.argv:
        install()

    if 'clean' in sys.argv:
        clean_chroot()

    if 'chroot' in sys.argv:
        shell_in_chroot("domogik")

    if 'chroot-clean' in sys.argv:
        shell_in_chroot("domogik_clean")

    if 'chroot-install' in sys.argv:
        chroot_intall()




