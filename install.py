#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import pwd
import sys
import platform
try:
    # from python3 onwards
    import configparser
except ImportError:
    # python 2
    import ConfigParser as configparser
import argparse
import shutil
import logging
import pkg_resources
from subprocess import Popen, PIPE, STDOUT
from distutils import version
import uuid


BLUE = '\033[94m'
OK = '\033[92m'
WARNING = '\033[93m'
FAIL = '\033[91m'
ENDC = '\033[0m'

### define display functions

def info(msg):
    logging.info(msg)
    print("{0} [ {1} ] {2}".format(BLUE, msg, ENDC))

def ok(msg):
    logging.info(msg)
    print("{0} ==> {1}  {2}".format(OK, msg, ENDC))

def warning(msg):
    logging.warning(msg)
    print("{0} ==> {1}  {2}".format(WARNING, msg, ENDC))

def fail(msg):
    logging.error(msg)
    print("{0} ==> {1}  {2}".format(FAIL, msg, ENDC))

def debug(msg):
    logging.debug(msg)

### test if script is launch as root

# CHECK run as root
info("Check this script is started as root")
assert os.getuid() == 0, "This script must be started as root"
ok("Correctly started with root privileges.")

logging.basicConfig(filename='install.log', level=logging.DEBUG)



### other functions

def get_c_hub():
    hub = {
        'x86_64' : 'src/domogik/xpl/tools/64bit/xPL_Hub',
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

def build_file_list(user):
    d_files = [
        ('/etc/domogik', [user, 0755], \
                ['src/domogik/examples/config/domogik.cfg.sample', \
                'src/domogik/xpl/hub/examples/config/xplhub.cfg.sample']),
        ('/var/cache/domogik', [user, None], []),
        ('/var/cache/domogik/pkg-cache', [user, None], []),
        ('/var/cache/domogik/cache', [user, None], []),
        ('/var/lib/domogik', [user, None], []),
        ('/var/lib/domogik/domogik_packages', [user, None], \
                ['src/domogik/common/__init__.py']),
        ('/var/lib/domogik/resources', [user, None], []),
        ('/var/lib/domogik/resources/butler', [user, None], []),
        ('/var/lib/domogik/resources', [user, None], \
                ['src/domogik/common/datatypes.json']),
        ('/var/lib/domogik/resources/sphinx', [user, None], \
                ['docs/Makefile',
                 'docs/conf-packages.py']),
        ('/var/lock/domogik', [user, 0755], []),
        ('/var/log/domogik', [user, 0755], []),
        ('/var/log/xplhub', [user, None], []),
    ]

    if os.path.exists('/etc/default'):
        debug("Found directory to store the system wide config: /etc/default")
        d_files.append(('/etc/default/', [user, None], \
                ['src/domogik/examples/default/domogik']))
    else:
        fail("Can't find directory where i can copy system wide config")
        exit(0)

    if os.path.exists('/etc/logrotate.d'):
        debug("Found a directory for the logrotate script: /etc/logrotate.d")
        d_files.append(('/etc/logrotate.d', ['root', None], \
                ['src/domogik/xpl/hub/examples/logrotate/xplhub']))

    if os.path.exists('/etc/init.d'):
        debug("Init script path is /etc/init.d")
        d_files.append(('/etc/init.d/', [user, 0755], \
                ['src/domogik/examples/init/domogik']))
    elif os.path.exists('/etc/rc.d'):
        debug("Init script path is /etc/rc.d")
        d_files.append(('/etc/rc.d/', [user, 0755], \
                ['src/domogik/examples/init/domogik']))
    else:
        warning("Can't find firectory for init script: Require manual install")

    hub = get_c_hub()
    if hub is not None:
        debug("Adding c hub path: {0}".format(hub))
        d_files.append(('/usr/sbin/', [user, None], [hub]))

    return d_files

def copy_files(user):
    info("Copy files")
    try:
        for directory, perm, files in build_file_list(user):
            if not os.path.exists(directory):
                if perm[1] != None:
                    res = os.makedirs(directory, int(perm[1]))
                else:
                    res = os.makedirs(directory)
                if not res:
                    ok("Creating dir {0}".format(directory))
                else:
                    fail("Failed creating dir {0}".format(directory))
            else:
                ok("Directory {0} already exists".format(directory))
            if perm[0] != '':
                debug("chown directory {0} with {1}".format(directory, perm[0]))
                os.system('chown {0} {1}'.format(perm[0], directory))
            for fname in files:
                # copy the file
                shutil.copy(os.path.join(\
                        os.path.dirname(os.path.realpath(__file__)), \
                            fname), \
                        directory)
                ok("Copyed file {0}".format(fname))
                dfname = os.path.join(directory, os.path.basename(fname))
                if perm[0] != '':
                    debug("chown dile {0} with {1}".format(dfname, perm[0]))
                    os.system('chown {0} {1}'.format(perm[0], dfname))
                #if perm[1] != None:
                #    os.system('chmod {0} {1}'.format(perm[1], dfname))

        # rename files
        os.rename('/var/lib/domogik/resources/sphinx/conf-packages.py', '/var/lib/domogik/resources/sphinx/conf.py')
    except:
        raise

def ask_user_name():
    info("Create domogik user")
    print("As what user should domogik run? [domogik]: "),
    new_value = sys.stdin.readline().rstrip('\n')
    if new_value == "":
        d_user = 'domogik'
    else:
        d_user = new_value
    debug("Username will be {0}".format(d_user))
    return d_user

def create_user(d_user, d_shell = "/bin/sh"):
    info("Create domogik user")
    if d_user not in [x[0] for x in pwd.getpwall()]:
        print("Creating the {0} user and add it to dialout".format(d_user))
        cmd_line = 'adduser --system {0} --shell {1} '.format(d_user, d_shell)
        debug(cmd_line)
        os.system(cmd_line)
        cmd_line = 'adduser {0} dialout'.format(d_user)
        debug(cmd_line)
        os.system(cmd_line)
    if d_user not in [x[0] for x in pwd.getpwall()]:
        fail("Failed to create domogik user")
    else:
        ok("Correctly created domogik user")
    # return the user to use

def is_domogik_advanced(advanced_mode, sect, key):
    advanced_keys = {
        'domogik': ['libraries_path', 'src_prefix', \
                'log_dir_path', 'pid_dir_path', 'broadcast', 'log_level', \
                'log_when', 'log_interval', 'log_backup_count'],
        'database': ['prefix', 'pool_recycle'],
        'admin': ['port', 'use_ssl', 'ssl_certificate', 'ssl_key', 'clean_json', 'rest_auth', 'secret_key'],
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

def is_xplhub_advanced(advanced_mode, sect, key):
    advanced_keys = {
        'hub': ['log_dir_path', 'log_bandwidth', 'log_invalid_data', 'log_level'],
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

def write_domogik_configfile(advanced_mode, intf):
    # read the sample config file
    newvalues = False
    config = configparser.RawConfigParser()
    config.read( ['/etc/domogik/domogik.cfg.sample'] )
    itf = ['bind_interface', 'interfaces']
    for sect in config.sections():
        info("Starting on section {0}".format(sect))
        if sect != "metrics":
            for item in config.items(sect):
                if sect == 'admin'and item[0] == 'secret_key':
                    config.set(sect, item[0], uuid.uuid4())
                elif item[0] in itf  and not advanced_mode:
                    config.set(sect, item[0], intf)
                    debug("Value {0} in domogik.cfg set to {1}".format(item[0], intf))
                elif is_domogik_advanced(advanced_mode, sect, item[0]):
                    print("- {0} [{1}]: ".format(item[0], item[1])),
                    new_value = sys.stdin.readline().rstrip('\n')
                    if new_value != item[1] and new_value != '':
                        # need to write it to config file
                        config.set(sect, item[0], new_value)
                        newvalues = True

        # manage metrics section
        else:
            config.set(sect, "id", uuid.getnode())   # set an unique id which is hardware dependent
            print("Set [{0}] : {1} = {2}".format(sect, id, uuid.getnode()))
            debug("Value {0} in domogik.cfg > [metrics] set to {1}".format(id, uuid.getnode()))

    # write the config file
    with open('/etc/domogik/domogik.cfg', 'wb') as configfile:
        ok("Writing the config file")
        config.write(configfile)

def write_xplhub_configfile(advanced_mode, intf):
    # read the sample config file
    newvalues = False
    config = configparser.RawConfigParser()
    config.read( ['/etc/domogik/xplhub.cfg.sample'] )
    for sect in config.sections():
        info("Starting on section {0}".format(sect))
        for item in config.items(sect):
            if item[0] == 'interfaces' and not advanced_mode:
                config.set(sect, item[0], intf)
                debug("Value {0} in xplhub.cfg set to {1}".format(item[0], intf))
            elif is_xplhub_advanced(advanced_mode, sect, item[0]):
                print("- {0} [{1}]: ".format(item[0], item[1])),
                new_value = sys.stdin.readline().rstrip('\n')
                if new_value != item[1] and new_value != '':
                    # need to write it to config file
                    config.set(sect, item[0], new_value)
                    newvalues = True
                debug("Value {0} in xplhub.cfg set to {1}".format(item[0], new_value))
    # write the config file
    with open('/etc/domogik/xplhub.cfg', 'wb') as configfile:
        ok("Writing the config file")
        config.write(configfile)

def write_domogik_configfile_from_command_line(args):
    # read the sample config file
    newvalues = False
    config = configparser.RawConfigParser()
    config.read( ['/etc/domogik/domogik.cfg.sample'] )
    for sect in config.sections():
        info("Starting on section {0}".format(sect))
        for item in config.items(sect):
            new_value = eval("args.{0}_{1}".format(sect, item[0]))
            if new_value != item[1] and new_value != '' and new_value != None:
                # need to write it to config file
                print("Set [{0}] : {1} = {2}".format(sect, item[0], new_value))
                config.set(sect, item[0], new_value)
                newvalues = True
            debug("Value {0} in domogik.cfg set to {1}".format(item[0], new_value))

    # write the config file
    with open('/etc/domogik/domogik.cfg', 'wb') as configfile:
        ok("Writing the config file")
        config.write(configfile)

def write_xplhub_configfile_from_command_line(args):
    # read the sample config file
    newvalues = False
    config = configparser.RawConfigParser()
    config.read( ['/etc/domogik/xplhub.cfg.sample'] )
    for sect in config.sections():
        info("Starting on section {0}".format(sect))
        for item in config.items(sect):
            new_value = eval("args.{0}_{1}".format(sect, item[0]))
            if new_value != item[1] and new_value != '' and new_value != None:
                # need to write it to config file
                print("Set [{0}] : {1} = {2}".format(sect, item[0], new_value))
                config.set(sect, item[0], new_value)
                newvalues = True
            debug("Value {0} in domogik.cfg set to {1}".format(item[0], new_value))
    # write the config file
    with open('/etc/domogik/xplhub.cfg', 'wb') as configfile:
        ok("Writing the config file")
        config.write(configfile)

def needupdate():
    # first check if there are already some config files
    if os.path.isfile("/etc/domogik/domogik.cfg") or \
       os.path.isfile("/etc/domogik/xplhub.cfg"):
        info("Configuration files")
        # DEL # print("Please notice that Domogik 0.3.x configuration files are no more compliant with Domogik 0.4 :")
        # DEL # print("- backup your Domogik 0.3 configuration files")
        # DEL # print("- say 'n' to the question to recreate them from scratch")
        print("Do you want to keep your current config files ? [Y/n]: ")
        new_value = sys.stdin.readline().rstrip('\n')
        if new_value == "y" or new_value == "Y" or new_value == '':
            debug("keeping curent config files")
            return False
        else:
            debug("NOT keeping curent config files")
            return True
    return True

def update_default(user):
    info("Update /etc/default/domogik")
    os.system('sed -i "s;^DOMOGIK_USER.*$;DOMOGIK_USER={0};" /etc/default/domogik'.format(user))

def find_interface():
    info("Trying to find an interface to listen on")
    try:
        import traceback
        pkg_resources.get_distribution("domogik").activate()
        from domogik.common.utils import get_interfaces, interface_has_ip
        for intf in get_interfaces():
            if intf == 'lo':
                continue
            if interface_has_ip(intf):
                break
    except:
        fail("Trace: {0}".format(traceback.format_exc()))
    else:
        ok("Selected interface {0}".format(intf))
    return intf

def install():
    parser = argparse.ArgumentParser(description='Domogik installation.')
    parser.add_argument('--dist-packages', dest='dist_packages', action="store_true",
                   default=False, help='Try to use distribution packages instead of pip packages')
    parser.add_argument('--no-create-database', dest='no_create_database', action="store_true",
                   default=False, help='create and allow domogik to access to it, if it is not already created')
    parser.add_argument('--no-setup', dest='setup', action="store_true",
                   default=False, help='Don\'t install the python packages')
    parser.add_argument('--no-test', dest='test', action="store_true",
                   default=False, help='Don\'t run a config test')
    parser.add_argument('--no-config', dest='config', action="store_true",
                   default=False, help='Don\'t run a config writer')
    parser.add_argument('--no-create-user', dest='user_creation', \
                   action="store_false", \
                   default=True, help='Don\'t create a user')
    parser.add_argument('--no-db-upgrade', dest='db', action="store_true",
                   default=False, help='Don\'t do a db upgrade')
    parser.add_argument('--no-mq-check', dest='mq', action="store_true",
                   default=False, help='Don\'t check the mq package')
    parser.add_argument('--no-db-backup', dest='skip_database_backup', action="store_true",
                   default=False, help='Don\'t do a db backup')
    parser.add_argument("--user",
                   help="Set the domogik user")
    parser.add_argument("--user-shell", dest="user_shell",
                   help="Set the domogik user shell")
    parser.add_argument('--advanced', dest='advanced_mode', action="store_true",
                   default=False, help='Allow to configure all options in interactive mode')

    # generate dynamically all arguments for the various config files
    # notice that we MUST NOT have the same sections in the different files!
    parser.add_argument('--command-line', dest='command_line', \
            action="store_true", default=False, \
            help='Configure the configuration files from the command line only')
    add_arguments_for_config_file(parser, \
            "src/domogik/examples/config/domogik.cfg.sample")
    add_arguments_for_config_file(parser, \
            "src/domogik/xpl/hub/examples/config/xplhub.cfg.sample")

    args = parser.parse_args()
    print args
    try:
        # CHECK python version
        if sys.version_info < (2, 6):
            fail("Python version is to low, at least python 2.6 is needed")
            exit(0)

        # CHECK sources not in / or /root
        info("Check the sources location (not in /root/ or /")
        print os.getcwd()
        assert os.getcwd().startswith("/root/") == False, "Domogik sources must not be located in the /root/ folder"

        # CHECK mq installed
        if not args.mq:
            info("Check that domogik-mq is installed")
            try:
                import domogikmq
            except ImportError:
                fail("Please install Domogik MQ first! (https://github.com/domogik/domogik-mq)")
                exit(0)

        # Execute database fix for some 0.2/0.3 databases
        #info("Process some database upgrade issues with previous releases")
        #cmd = "sh ./src/domogik/install/db_fix_03.sh"
        #p = Popen(cmd, shell=True, stdin=PIPE, stdout=PIPE, stderr=STDOUT)
        #lines_iterator = iter(p.stdout.readline, b"")
        #for line in lines_iterator:
        #    print(line)


        if args.dist_packages:
            dist_packages_install_script = ''
            #platform.dist() and platform.linux_distribution() 
            #doesn't works with ubuntu/debian, both say debian.
            #So I not found pettiest test :(
            if os.system(' bash -c \'[ "`lsb_release -si`" == "Debian" ]\'') == 0:
                dist_packages_install_script = './debian_packages_install.sh'
            elif os.system(' bash -c \'[ "`lsb_release -si`" == "Ubuntu" ]\'') == 0:
                dist_packages_install_script = './debian_packages_install.sh'
            elif os.system(' bash -c \'[ "`lsb_release -si`" == "Raspbian" ]\'') == 0:
                dist_packages_install_script = './debian_packages_install.sh'
            if dist_packages_install_script == '' :
                raise OSError("The option --dist-packages is not implemented on this distribution. \nPlease install the packages manually.\n When packages have been installed, you can re reun the installation script without the --dist-packages option.")
            if os.system(dist_packages_install_script) != 0:
                raise OSError("Cannot install packages correctly script '%s'" % dist_packages_install_script)

        # RUN setup.py
        if not args.setup:
            info("Run setup.py")
            if os.system('python setup.py develop') !=  0:
                raise OSError("setup.py doesn't finish correctly")

        # ask for the domogik user
        if args.user == None or args.user == '':
            user = ask_user_name()
        else:
            ok("User setted to '{0}' from the command line".format(args.user))
            user = args.user

        # create user
        if args.user_creation:
            if args.user_shell:
                create_user(user, args.user_shell)
            else:
                create_user(user)

        # Copy files
        copy_files(user)
        update_default(user)

        # write config file
        if args.command_line:
            info("Update the config file : /etc/domogik/domogik.cfg")
            write_domogik_configfile_from_command_line(args)
            info("Update the config file : /etc/domogik/xplhub.cfg")
            write_xplhub_configfile_from_command_line(args)
        else:
            if not args.config and needupdate():
                # select the correct interface
                intf = find_interface()
                # update the config file
                info("Update the config file : /etc/domogik/domogik.cfg")
                write_domogik_configfile(args.advanced_mode, intf)
                info("Update the config file : /etc/domogik/xplhub.cfg")
                write_xplhub_configfile(args.advanced_mode, intf)

        # upgrade db
        if not args.db:

            # check if alembic version is at least 0.7.4. Else raise an error
            from alembic import __version__ as alembic_version
            if version.StrictVersion(alembic_version) < version.StrictVersion("0.7.4"):
                fail("The 'alembic' version installed on this system ({0}) is not recent enough. Please install at least alembic >= 0.7.4".format(alembic_version))
                exit(0)

            # do db upgrade
            try:
                user_entry = pwd.getpwnam(user)
            except KeyError:
                raise KeyError("The user %s does not exists, you MUST create it or change the DOMOGIK_USER parameter in %s. Please report this as a bug if you used install.sh." % (user, file))

            # launch db_install as the domogik user
            #uid = user_entry.pw_uid
            #user_home = user_entry.pw_dir
            #os.setreuid(0,uid)
            #old_home = os.environ['HOME']
            #os.environ['HOME'] = user_home
            #os.system('python src/domogik/install/db_install.py')
            #os.setreuid(0,0)
            #os.environ['HOME'] = old_home

              
            try:
                import traceback
                # we must activate the domogik module as setup.py is launched from install.py and just after we try 
                # to import something from the domogik package but the module is not known without doing anything...
                pkg_resources.get_distribution("domogik").activate()
                from domogik.install.db_install import DbInstall
            except:
                print("Trace: {0}".format(traceback.format_exc()))

            dbi = DbInstall()
            if not args.no_create_database:
                dbi.create_db()
            dbi.install_or_upgrade_db(args.skip_database_backup)

            # change permissions to some files created as root during the installation to the domogik user
            os.chown("/var/log/domogik/db_api.log", user_entry.pw_uid, -1)
            os.chown("/var/lock/domogik/config.lock", user_entry.pw_uid, -1)


        if not args.test:
            os.system('python test_config.py')
        print("\n\n")
    except:
        import traceback
        print "========= TRACEBACK ============="
        print traceback.format_exc()
        print "================================="
        fail(sys.exc_info())

def add_arguments_for_config_file(parser, fle):
    # read the sample config file
    config = configparser.RawConfigParser()
    config.read( [fle] )
    for sect in config.sections():
        for item in config.items(sect):
            key = "{0}_{1}".format(sect, item[0])
            parser.add_argument("--{0}".format(key),
                help="Update section {0}, key {1} value".format(sect, item[0]))

if __name__ == "__main__":
    install()
