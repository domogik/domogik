#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import pwd
import sys
import platform
import ConfigParser
import argparse
import shutil

BLUE = '\033[94m'
OK = '\033[92m'
WARNING = '\033[93m'
FAIL = '\033[91m'
ENDC = '\033[0m'

def info(msg):
    print("%s [ %s ] %s" % (BLUE,msg,ENDC))
def ok(msg):
    print("%s ==> %s  %s" % (OK,msg,ENDC))
def warning(msg):
    print("%s ==> %s  %s" % (WARNING,msg,ENDC))
def fail(msg):
    print("%s ==> %s  %s" % (FAIL,msg,ENDC))

def get_c_hub():
    hub = {
        'x86_64' : 'src/domogik/pl/tools/64bit/xPL_Hub',
        'i686' : 'src/domogik/xpl/tools/32bit/xPL_Hub',
        'arm' : 'src/domogik/xpl/tools/arm/xPL_Hub',
        'armv5tel' : 'src/domogik/xpl/tools/arm/xPL_Hub',
        'armv6l' : 'src/domogik/xpl/tools/arm/xPL_Hub'
    }
    arch = platform.machine()
    if arch in hub.keys():
        return hub[arch]
    else:
        return None

def build_file_list():
    d_files = [
        ('/etc/domogik', ['domogik:domogik', ''], ['src/domogik/examples/config/domogik.cfg',  'src/domogik/examples/packages/sources.list', 'src/domogik/xplhub/examples/config/xplhub.cfg']),
        ('/var/cache/domogik', ['domogik:domogik', ''], []),
        ('/var/cache/domogik/pkg-cache', ['domogik:domogik', ''], []),
        ('/var/cache/domogik/cache', ['domogik:domogik', ''], []),
        ('/var/lib/domogik', ['domogik:domogik', ''], []),
        ('/var/lib/domogik/packages', ['domogik:domogik', ''], ['src/domogik/common/__init__.py']),
        ('/var/lib/domogik/resources', ['domogik:domogik', ''], []),
        ('/var/lib/domogik/resources', ['domogik:domogik', ''], ['src/domogik/common/datatypes.json']),
        ('/var/lock/domogik', ['domogik:domogik', ''], []),
    ]

    if os.path.exists('/etc/default'):
        d_files.append(('/etc/default/', ['root:root', ''], ['src/domogik/examples/default/domogik']))
    else:
        print "Can't find directory where i can copy system wide config"
        exit(0)

    if os.path.exists('/etc/logrotate.d'):
        d_files.append(('/etc/logrotate.d', ['root:root', ''], ['src/domogik/examples/logrotate/domogik', 'src/domogik/xplhub/examples/logrotate/xplhub']))

    if os.path.exists('/etc/init.d'):
        d_files.append(('/etc/init.d/', ['root:root', ''], ['src/domogik/examples/init/domogik']))
    elif os.path.exists('/etc/rc.d'):
        d_files.append(('/etc/rc.d/', ['root:root', ''], ['src/domogik/examples/init/domogik']))
    else:
        print("Can't find firectory for init script")
        exit(0)

    hub = get_c_hub()
    if hub is not None:
        d_files.append(('/usr/sbin/', ['root:root', ''], [hub]))

    return d_files

def copy_files():
    info("Copy files")
    print build_file_list()
    for directory, perm, files in build_file_list():
        print directory
        if not os.path.exists(directory):
            if os.makedirs(directory):
                ok("Creating dir {0}".format(directory))
            else:
                fail("Creating dir {0}".format(directory))
            # TODO set correct permissions
        for fname in files:
            # copy the file
            dst_fname = os.path.join(directory, fname)
            if os.path.exists(dst_fname):
                os.removed(dst_fname)
            if shutil.copy(os.path.join(os.path.dirname(os.path.realpath(__file__)), fname), directory):
                ok("Copyed file {0}".format(fname))
                # TODO file permisions

def create_user():
    info("Create domogik user")
    print("As what user should domogik run? [domogik]: "),
    newValue = sys.stdin.readline().rstrip('\n')
    if newValue == "":
        d_user = 'domogik'
    else:
        d_user = newValue
    if d_user not in [x[0] for x in pwd.getpwall()]:
        print("Creating the {0} user".format(d_user))
        os.system('/usr/sbin/useradd --system {0}'.format(d_user))
    if d_user not in [x[0] for x in pwd.getpwall()]:
        fail("Failed to create domogik user")
    else:
        ok("Correctly created domogik user")

def is_advanced(advanced_mode, sect, key):
    advanced_keys = {
        'domogik': ['libraries_path', 'src_prefix', 'log_dir_path', 'pid_dir_path', 'broadcast'],
        'database': ['db_prefix', 'pool_recycle'],
        'rest': ['rest_server_port', 'rest_use_ssl', 'rest_ssl_certificate'],
        'mq': ['req_rep_port', 'pub_port', 'sub_port'],
    }
    if advanced_mode:
        return True
    else:
        if sect not in advanced_keys:
            return True
        else:
            if key not in advanced_keys[sect]:
                return True
            else:
                return False

def write_configfile(advanced_mode):
    # read the config file
    newvalues = False
    config = ConfigParser.RawConfigParser()
    config.read( ['/etc/domogik/domogik.cfg'] )
    for sect in config.sections():
        info("Starting on section {0}".format(sect))
        for item in config.items(sect):
            if is_advanced(advanced_mode, sect, item[0]):
                print("Key {0} [{1}]: ".format(item[0], item[1])),
                newValue = sys.stdin.readline().rstrip('\n')
                if newValue != item[1] and newValue != '':
                    # need to write it to config file
                    config.set(sect, item[0], newValue)
                    newvalues = True
    if newvalues:
        # write the config file
        with open('/etc/domogik/domogik.cfg', 'wb') as configfile:
            ok("Writing the config file")
            config.write(configfile)

def needupdate():
    print("Do you want to keep your current config file? [Y/n]: "),
    newValue = sys.stdin.readline().rstrip('\n')
    if newValue == "y" or newValue == "Y" or newValue == '':
        return False
    else:
        return True

def config(advanced, notest):
    try:
        am_i_root()
        if needupdate():
            write_configfile(advanced)
        if not notest:
            test_config()
    except:
        fail(sys.exc_info())


def install():
    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('--no-setup', dest='setup', action="store_true",
                   default=False, help='Don\'t install the python packages')
    parser.add_argument('--no-test', dest='test', action="store_true",
                   default=False, help='Don\'t run a config test')
    parser.add_argument('--no-config', dest='config', action="store_true",
                   default=False, help='Don\'t run a config writer')
    parser.add_argument('--no-create-user', dest='user', action="store_true",
                   default=False, help='Don\'t create a user')
    parser.add_argument('--no-db-upgrade', dest='db', action="store_true",
                   default=False, help='Don\'t do a db upgrade')
    args = parser.parse_args()
    # CHECK python version
    if sys.version_info < (2,6):
        print "Python version is to low, at least python 2.6 is needed"
        exit(0)
    # CHECK run as root
    info("Check this script is started as root")
    assert os.getuid() == 0, "This script must be started as root"
    ok("Correctly started with root privileges.")
    # RUN setup.py
    if not args.setup:
        info("Run setup.py")
        os.system('python setup.py develop')
    # Copy files
    copy_files()
    # create user
    if not args.user:
        create_user()
    # write config file
    if not args.config and needupdate():
        write_configfile(False)
    # upgrade db
    if not args.db:
        os.system('python src/domogik/install/installer.py')
    #if not args.test:
    # run test config
    print("\n\n")
    ok("================================================== <==")
    ok(" Everything seems ok, you should be able to start  <==")
    ok("      Domogik with /etc/init.d/domogik start       <==")
    ok("            or /etc/rc.d/domogik start             <==")
    ok(" You can now install Domoweb User Interface        <==")
    ok("================================================== <==")

if __name__ == "__main__":
    install()

