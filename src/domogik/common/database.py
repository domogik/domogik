# -*- coding: utf-8 -*-

""" This file is part of B{Domogik} project (U{http://www.domogik.org}).

License
=======

B{Domogik} is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

B{Domogik} is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Domogik. If not, see U{http://www.gnu.org/licenses}.

Module purpose
==============

API to use Domogik database.
Please don't forget to add unit test in 'database_test.py' if you add a new
method. Please always run 'python database_test.py' if you change something in
this file.

Implements
==========

- class DbHelperException(Exception) : exceptions linked to the DbHelper class
- class DbHelper : API to use Domogik database

@author: Maxence DUNNEWIND / Marc SCHNEIDER
@copyright: (C) 2007-2012 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

import datetime, hashlib, time

import json
import sqlalchemy
from sqlalchemy import Table, MetaData, and_, or_, not_
from sqlalchemy.sql.expression import func, extract
from sqlalchemy.orm import sessionmaker, defer

from domogik.common.utils import ucode
from domogik.common import logger
#from domogik.common.packagejson import PackageJson
from domogik.common.configloader import Loader
from domogik.common.sql_schema import (
        Device, DeviceStats, DeviceParam,
        PluginConfig, Person,
        UserAccount,
        Scenario, ScenarioUUID,
        Command, CommandParam,
        Sensor, SensorHistory,
        XplCommand, XplStat, XplStatParam, XplCommandParam
)
from contextlib import contextmanager

DEFAULT_RECYCLE_POOL = 3600


def _make_crypted_password(clear_text_password):
    """Make a crypted password (using sha256)

    @param clear_text_password : password in clear text
    @return crypted password

    """
    password = hashlib.sha256()
    password.update(clear_text_password)
    return password.hexdigest()

def _datetime_string_from_tstamp(ts):
    """Make a date from a timestamp"""
    return str(datetime.datetime.fromtimestamp(ts))

def _get_week_nb(dt):
    """Return the week number of a datetime expression"""
    #return (dt - datetime.datetime(dt.year, 1, 1)).days / 7
    return dt.isocalendar()[1]

class DbHelperException(Exception):
    """This class provides exceptions related to the DbHelper class
    """

    def __init__(self, value):
        """Class constructor

        @param value : value of the exception

        """
        Exception.__init__(self, value)
        self.value = value

    def __str__(self):
        """Return the object representation

        @return value of the exception

        """
        return repr(self.value)


class DbHelper():
    """This class provides methods to fetch and put informations on the Domogik database

    The user should only use methods from this class and don't access the database directly

    """
    __engine = None
    __session = None
    __session_object = None

    def __init__(self, echo_output=False, use_test_db=False, engine=None):
        """Class constructor

        @param echo_output : if True displays sqlAlchemy queries (optional, default False)
        @param use_test_db : if True use a test database (optional, default False)
        @param engine : an existing engine, if not provided, a new one will be created
        """
        # Here you have to specify twice the logger name as two instances of DbHelper are created
        self.log = logger.Logger('db_api').get_logger('db_api')
        
        cfg = Loader('database')
        config = cfg.load()
        self.__db_config = dict(config[1])

        if self.__db_config.has_key("recycle_pool"):
            #self.log.info(u"User value for recycle pool : {0}".format(self.__db_config['recycle_pool']))
            pool_recycle = int(self.__db_config['recycle_pool'])
        else:
            #self.log.info(u"No user value for recycle pool. Using default value : {0}".format(DEFAULT_RECYCLE_POOL))
            pool_recycle = DEFAULT_RECYCLE_POOL

        if config[0]['log_level'] == 'debug':
            #logger.Logger('sqlalchemy.engine', domogik_prefix=False, use_filename='sqlalchemy')
            #logger.Logger('sqlalchemy.pool', domogik_prefix=False, use_filename='sqlalchemy')
            #logger.Logger('sqlalchemy.orm', domogik_prefix=False, use_filename='sqlalchemy')
            pass

        url = self.get_url_connection_string()
        if use_test_db:
            url = '%s_test' % url
        # Connecting to the database
        if DbHelper.__engine == None:
            if engine != None:
                DbHelper.__engine = engine
            else:
                DbHelper.__engine = sqlalchemy.create_engine(url, echo = echo_output, encoding='utf8', 
                                                             pool_recycle=pool_recycle, pool_size=20, max_overflow=10)
        if DbHelper.__session_object == None:
            DbHelper.__session_object = sessionmaker(bind=DbHelper.__engine, autoflush=True)
        #self.__session = DbHelper.__session_object()

    @contextmanager
    def session_scope(self):
        self.__session = DbHelper.__session_object()
        try:
            yield self.__session
            self.__session.commit()
        except:
            self.__session.rollback()
            raise
        finally:
            self.__session.close()
            self.__session = None

    def open_session(self):
        self.__session = DbHelper.__session_object()

    def close_session(self):
        self.__session.close()
        self.__session = None

    def get_engine(self):
        """Return the existing engine or None if not set
        @return self.__engine

        """
        return DbHelper.__engine

    def __del__(self):
        if self.__session:
            self.__session.close()

    def __rollback(self):
        """Issue a rollback to a SQL transaction (for dev purposes only)

        """
        self.__session.rollback()

    def get_url_connection_string(self):
        """Get url connection string to the database reading the configuration file"""
        if self.__db_config['type'] == "mysql":
            url = "mysql+pymysql://"
        else:
            url = "%s://" % self.__db_config['type']
        if self.__db_config['port'] != '':
            url = "%s%s:%s@%s:%s/%s" % (url, self.__db_config['user'], self.__db_config['password'],
                                        self.__db_config['host'], self.__db_config['port'], self.__db_config['name'])
        else:
            url = "%s%s:%s@%s/%s" % (url, self.__db_config['user'], self.__db_config['password'],
                                     self.__db_config['host'], self.__db_config['name'])
        return url
    
    def get_db_user(self):
        return self.__db_config['user']

    def get_db_password(self):
        return self.__db_config['password']
    
    def get_db_name(self):
        return self.__db_config['name']

    def is_db_type_mysql(self):
        return self.__db_config['type'].lower() == 'mysql'

    def get_db_type(self):
        """Return DB type which is currently used (mysql, postgresql)"""
        return self.__db_config['type'].lower()

####
# Plugin config
####
    def list_all_plugin_config(self):
        """Return a list of all plugin config parameters

        @return a list of PluginConfig objects

        """
        return self.__session.query(PluginConfig).all()

    def list_plugin_config(self, pl_id, pl_hostname):
        """Return all parameters of a plugin

        @param pl_id : plugin id
        @param pl_hostname : hostname the plugin is installed on
        @return a list of PluginConfig objects

        """
        return self.__session.query(
                        PluginConfig
                    ).filter_by(id=ucode(pl_id)
                    ).filter_by(hostname=ucode(pl_hostname)
                    ).all()

    def get_plugin_config(self, pl_id, pl_hostname, pl_key):
        """Return information about a plugin parameter

        @param pl_id : plugin id
        @param pl_hostname : hostname the plugin is installed on
        @param pl_key : key we want the value from
        @return a PluginConfig object

        """
        try:
            ret = self.__session.query(
                        PluginConfig
                    ).filter_by(id=ucode(pl_id)
                    ).filter_by(hostname=ucode(pl_hostname)
                    ).filter_by(key=ucode(pl_key)
                    ).first()
        except:
            self.log.debug(u"oups : {0}".format(traceback.format-exc()))
        return ret

    def set_plugin_config(self, pl_id, pl_hostname, pl_key, pl_value):
        """Add / update a plugin parameter

        @param pl_id : plugin id
        @param pl_hostname : hostname the plugin is installed on
        @param pl_key : key we want to add / update
        @param pl_value : key value we want to add / update
        @return : the added / updated PluginConfig item

        """
        # Make sure previously modified objects outer of this method won't be commited
        self.__session.expire_all()
        plugin_config = self.__session.query(
                                PluginConfig
                            ).filter_by(id=ucode(pl_id)
                            ).filter_by(hostname=ucode(pl_hostname)
                            ).filter_by(key=ucode(pl_key)).first()
        if not plugin_config:
            plugin_config = PluginConfig(id=pl_id, hostname=pl_hostname, key=pl_key, value=pl_value)
        else:
            plugin_config.value = ucode(pl_value)
        self.__session.add(plugin_config)
        try:
            self.__session.commit()
        except Exception as sql_exception:
            self.__raise_dbhelper_exception("SQL exception (commit) : %s" % sql_exception, True)
        return plugin_config

    def del_plugin_config(self, pl_id, pl_hostname):
        """Delete all parameters of a plugin config

        @param pl_id : plugin id
        @param pl_hostname : hostname the plugin is installed on
        @return the deleted PluginConfig objects

        """
        # Make sure previously modified objects outer of this method won't be commited
        self.__session.expire_all()
        plugin_config_list = self.__session.query(
                                    PluginConfig
                                ).filter_by(id=ucode(pl_id)
                                ).filter_by(hostname=ucode(pl_hostname)).all()
        for plc in plugin_config_list:
            self.__session.delete(plc)
        try:
            self.__session.commit()
        except Exception as sql_exception:
            self.__raise_dbhelper_exception("SQL exception (commit) : " % sql_exception, True)
        return plugin_config_list

    def del_plugin_config_key(self, pl_id, pl_hostname, pl_key):
        """Delete a key of a plugin config

        @param pl_id : plugin id
        @param pl_hostname : hostname the plugin is installed on
        @param pl_key : key of the plugin config
        @return the deleted PluginConfig object

        """        
        # Make sure previously modified objects outer of this method won't be commited
        self.__session.expire_all()
        plugin_config = self.__session.query(
                               PluginConfig
                           ).filter_by(id=ucode(pl_id)
                           ).filter_by(hostname=ucode(pl_hostname)
                           ).filter_by(key=ucode(pl_key)).first()
        if plugin_config is not None:
            self.__session.delete(plugin_config)
            try:
                self.__session.commit()
            except Exception as sql_exception:
                self.__raise_dbhelper_exception("SQL exception (commit) : " % sql_exception, True)
        return plugin_config
        
###
# Devices
###
    def list_devices(self):
        """Return a list of devices
        @return a list of Device objects (only the devices that are known by this realease)
        """
        #return self.__session.query(Device).filter(Device.address==None).all()
        device_list = []
        for device in self.__session.query(Device).filter(Device.address==None).all():
            device_list.append(self.get_device(device=device))
        return device_list

    def list_devices_by_plugin(self, p_id):
        #return self.__session.query(Device).filter_by(client_id=p_id).all()
        device_list = []
        for device in self.__session.query(Device).filter_by(client_id=p_id).all():
            device_list.append(self.get_device(device=device))
        return device_list

    def list_old_devices(self):
        """Return a list of devices
        @return a list of Device objects (only the devices that are inot known by this realease)
        """
        return self.__session.query(Device).filter(Device.address!=None).all()

    def get_device(self, d_id=None, device=None):
        """Return a device by its id

        @param d_id : The device id
        @param device : The Device object (sqlalchemy)
        @return a Device object

        """
        if device is None and d_id is not None:
            device = self.__session.query(Device).filter_by(id=d_id).first()
        
        if device == None:
            return None
        # fill basic informations about the device
        json_device = { 'id' : device.id, 
                        'name' : device.name, 
                        'reference' : device.reference, 
                        'description' : device.description, 
                        'device_type_id' : device.device_type_id, 
                        'client_id' : device.client_id
                      }
        # params
        json_device['params'] = {}
        for a_param in device.params:
            json_param = { 'id': a_param.id,
                           'key': a_param.key,
                           'type': a_param.type,
                           'value': a_param.value
                           }
            json_device['parameters'][a_param.key] = json_param
        
        # complete with sensors informations
        json_device['sensors'] = {}
        for a_sensor in device.sensors:
            json_sensor = { 'id' : a_sensor.id,
                            'name' : a_sensor.name,
                            'data_type' : a_sensor.data_type,
                            'conversion' : a_sensor.conversion, 
                            'last_value' : a_sensor.last_value, 
                            'last_received' : a_sensor.last_received,
                            'reference' : a_sensor.reference
                          }
            json_device['sensors'][a_sensor.reference] = json_sensor

        # complete with commands information
        json_device['commands'] = {}
        for a_cmd in device.commands:
            json_command = {
                    'id': a_cmd.id,
                    'name': a_cmd.name,
                    'return_confirmation': a_cmd.return_confirmation,
                    'xpl_command' : a_cmd.xpl_command.json_id,
                    'parameters': []
                    }
            for a_cmd_param in a_cmd.params:
                json_command['parameters'].append({ 'key': a_cmd_param.key,
                                                    'data_type': a_cmd_param.data_type,
                                                    'conversion': a_cmd_param.conversion
                                                })
            json_device['commands'][a_cmd.reference] = json_command

        # complete for each xpl_stat information
        json_device['xpl_stats'] = {}
        for a_xplstat in device.xpl_stats:
            json_xplstat = { 'id' : a_xplstat.id,
                             'json_id' : a_xplstat.json_id,
                             'name' : a_xplstat.name,
                             'schema' : a_xplstat.schema,
                             'parameters' : {
                                'static' : [],
                                'dynamic' : []
                             }
                           }
            # and for each xpl_stat, add the parameters informations
            # the loop is done twice : 
            # - for the dynamic parameters
            # - for the static parameters
            for a_xplstat_param in a_xplstat.params:
                if a_xplstat_param.static == False and a_xplstat_param.sensor_id is not None:
                    if a_xplstat_param.sensor_id:
                        for sen in device.sensors:
                            if sen.id == a_xplstat_param.sensor_id:
                                sensor_name = sen.reference
                    else:
                        sensor_name = None
                    json_xplstat['parameters']['dynamic'].append({ 'key' :  a_xplstat_param.key,
                                                                   'ignore_values' :  a_xplstat_param.ignore_values,
                                                                   'sensor_name': sensor_name
                                                                })
                else:
                    json_xplstat['parameters']['static'].append({ 'key' :  a_xplstat_param.key,
                                                                  'type' : a_xplstat_param.type,
                                                                  'value' :  a_xplstat_param.value,
                                                                })
                 
            json_device['xpl_stats'][a_xplstat.json_id] = json_xplstat

        # xpl_commands
        json_device['xpl_commands'] = {}
        for a_xplcmd in device.xpl_commands:
            json_xplcmd = { 'id': a_xplcmd.id,
                            'name' : a_xplcmd.name,
                            'schema' : a_xplcmd.schema,
                            'xpl_stat_ack': a_xplcmd.stat.json_id,
                            'parameters' : []
                            }
            for a_xplcmd_param in a_xplcmd.params:
                json_xplcmd['parameters'].append({ 'key' :  a_xplcmd_param.key,
                                                   'value' :  a_xplcmd_param.value
                                                })
            json_device['xpl_commands'][a_xplcmd.json_id] = json_xplcmd
        return json_device


    def add_device_and_commands_xplstat(self, devid, sensorid, a_xplstat, xplstat_in_client_data):
        self.log.debug(u"Device creation : adding xplstats '{0}'...".format(xplstat_in_client_data['name']))
        xplstat = XplStat(name = xplstat_in_client_data['name'], \
              schema = xplstat_in_client_data['schema'], \
              device_id = devid, \
              json_id = a_xplstat)
        self.__session.add(xplstat)
        self.__session.flush()

        ### Table core_xplstat_param
        #- if static field == 1 => this is a static param
        #- if static field == 0 and no sensor id is defined => this is a device param => value will be filled in
        #- if statis == 0 and it has a sensor id => its a dynamic param

        # static parameters
        for a_parameter in xplstat_in_client_data['parameters']['static']:
            self.log.debug(u"Device creation : inserting data in core_xplstat_param for '{0} : static {1}'...".format(a_xplstat, a_parameter))
            parameter =  XplStatParam(xplstat_id = xplstat.id , \
                                      sensor_id = sensorid, \
                                      key = a_parameter['key'], \
                                      value = a_parameter['value'], \
                                      static = True, \
                                      ignore_values = None,
                                      type = None)
            self.__session.add(parameter)
            self.__session.flush()

        # dynamic parameters
        for a_parameter in xplstat_in_client_data['parameters']['dynamic']: 
            self.log.debug(u"Device creation : inserting data in core_xplstat_param for '{0} : dynamic {1}'...".format(a_xplstat, a_parameter))
            # set some values before inserting data
            if 'ignore_values' not in a_parameter:
                a_parameter['ignore_values'] = None
            parameter =  XplStatParam(xplstat_id = xplstat.id , \
                                      sensor_id = sensorid, \
                                      key = a_parameter['key'], \
                                      value = None, \
                                      static = False, \
                                      ignore_values = a_parameter['ignore_values'],
                                      type = None)
            self.__session.add(parameter)
            self.__session.flush()

        # device parameters
        # => nothing to do
        return xplstat 


    def add_device_and_commands(self, name, device_type, client_id, description, reference, client_data):
        """ Create a device : fill the following tables with data from the related client json file
            - core_device
            - ...
        """
        created_xpl_stats = {}
        self.__session.expire_all()

        ### Add the device itself
        self.log.debug(u"Device creation : inserting data in core_device...")
        device = Device(name=name, device_type_id=device_type, \
                client_id=client_id, client_version=client_data['identity']['version'], \
                description=description, reference=reference)
        self.__session.add(device)
        self.__session.flush()

        ### Table core_sensor
        # first, get the sensors associated to the device_type
        self.log.debug(u"Device creation : start to process the sensors")
        device_type_sensors = client_data['device_types'][device_type]['sensors']
        self.log.debug(u"Device creation : list of sensors available for the device : {0}".format(device_type_sensors))

        # then, for each sensor, create it in databse for the device
        for a_sensor in device_type_sensors:
            self.log.debug(u"Device creation : inserting data in core_sensor for '{0}'...".format(a_sensor))
            sensor_in_client_data = client_data['sensors'][a_sensor]
            sensor = Sensor(name = sensor_in_client_data['name'], \
                            device_id  = device.id, \
                            reference = a_sensor, \
                            data_type = sensor_in_client_data['data_type'], \
                            conversion = sensor_in_client_data['conversion'], \
                            h_store = sensor_in_client_data['history']['store'], \
                            h_max = sensor_in_client_data['history']['max'], \
                            h_expire = sensor_in_client_data['history']['expire'], \
                            h_round = sensor_in_client_data['history']['round_value'], \
                            )
            self.__session.add(sensor)
            self.__session.flush()

            ### Table core_xplstat
            # for each sensor, insert its xplstats (if any) in database
            self.log.debug(u"Device creation : inserting data in core_xplstat for '{0}'...".format(a_sensor))
            # find all xpl_stats that link to this sensor and insert them
            for a_xplstat in client_data['xpl_stats']:
                xplstat_in_client_data = client_data['xpl_stats'][a_xplstat]
                for param in xplstat_in_client_data['parameters']['dynamic']:
                    if 'sensor' in param and param['sensor'] == a_sensor:
                        xplstat = self.add_device_and_commands_xplstat(device.id, sensor.id, a_xplstat, xplstat_in_client_data)
                        created_xpl_stats[a_xplstat] = xplstat.id

        ### Table core_command

        # first, get the commands associated to the device_type
        self.log.debug(u"Device creation : start to process the commands")
        device_type_commands = client_data['device_types'][device_type]['commands']
        self.log.debug(u"Device creation : list of commands available for the device : {0}".format(device_type_commands))

        for a_command in device_type_commands:
            self.log.debug(u"Device creation : inserting data in core_command for '{0}'...".format(a_command))
            command_in_client_data = client_data['commands'][a_command]
            command = Command(name = command_in_client_data['name'], \
                              device_id = device.id, \
                              reference = a_command, \
                              return_confirmation = command_in_client_data['return_confirmation'])
            self.__session.add(command)
            self.__session.flush()

            self.log.debug(u"Device creation : inserting data in core_command_param for '{0}'...".format(a_command))
            for command_param in client_data['commands'][a_command]['parameters']:
                pa = CommandParam(command.id, \
                                  command_param['key'], \
                                  command_param['data_type'], \
                                  command_param['conversion'])
                self.__session.add(pa)
                self.__session.flush()

            ### Table core_xplcommand
            if 'xpl_command' in command_in_client_data:
                self.log.debug(u"Device creation : inserting data in core_xplcommand for '{0}'...".format(a_command))
                x_command = client_data['xpl_commands'][command_in_client_data['xpl_command']]
                if x_command['xplstat_name'] in created_xpl_stats.keys():
                    xplstatid = created_xpl_stats[x_command['xplstat_name']]
                else:
                    xplstat_in_client_data = client_data['xpl_stats'][x_command['xplstat_name']]
                    xplstat = self.add_device_and_commands_xplstat(device.id, None, x_command['xplstat_name'], xplstat_in_client_data)
                    xplstatid = xplstat.id
                xplcommand = XplCommand(cmd_id=command.id, \
                                        name=x_command['name'], \
                                        schema=x_command['schema'], \
                                        device_id=device.id, stat_id=xplstatid, \
                                        json_id=command_in_client_data['xpl_command'])
                self.__session.add(xplcommand)
                self.__session.flush()
                ### Table core_xplcommand_param
                for p in x_command['parameters']['static']:
                    par = XplCommandParam(cmd_id=xplcommand.id, \
                                         key=p['key'], value=p['value'])
                    self.__session.add(par)

        ### Finally, commit all !
        try:
            self.__session.commit()
        except Exception as sql_exception:
            self.__raise_dbhelper_exception("SQL exception (commit) : %s" % sql_exception, False)

        ### Return the created device as json
        d = self.get_device(device.id)
        return d

    def add_device(self, d_name, d_type_id, d_client_id, d_description=None, d_reference=None):
        """Add a device item

        @param d_name : name of the device
        @param d_type_id : device type id (x10.Switch, x10.Dimmer, Computer.WOL...)
        @param d_client_id : the plugin that controls this device
        @param d_description : extended device description, optional
        @param d_reference : device reference (ex. AM12 for x10), optional
        @return the new Device object

        """
        # Make sure previously modified objects outer of this method won't be commited
        self.__session.expire_all()
        device = Device(name=d_name, description=d_description, reference=d_reference, \
                        device_type_id=d_type_id, client_id=d_client_id)
        self.__session.add(device)
        try:
            self.__session.commit()
        except Exception as sql_exception:
            self.__raise_dbhelper_exception("SQL exception (commit) : %s" % sql_exception, True)
        return device

    def update_device(self, d_id, d_name=None, d_description=None, d_reference=None, d_address=None):
        """Update a device item

        If a param is None, then the old value will be kept

        @param d_id : Device id
        @param d_name : device name (optional)
        @param d_description : Extended item description (optional)
        @return the updated Device object

        """
        # Make sure previously modified objects outer of this method won't be commited
        self.__session.expire_all()
        device = self.__session.query(Device).filter_by(id=d_id).first()
        if device is None:
            self.__raise_dbhelper_exception("Device with id %s couldn't be found" % d_id)
        if d_name is not None:
            device.name = ucode(d_name)
        if d_address is not None:
            device.address = ucode(d_address)
        if d_description is not None:
            if d_description == '': d_description = None
            device.description = ucode(d_description)
        if d_reference is not None:
            if d_reference == '': d_reference = None
            device.reference = ucode(d_reference)
        self.__session.add(device)
        try:
            self.__session.commit()
        except Exception as sql_exception:
            self.__raise_dbhelper_exception("SQL exception (commit) : %s" % sql_exception, True)
        return device

    def del_device(self, d_id):
        """Delete a device

        @param d_id : device id
        @return the deleted device

        """
        # Make sure previously modified objects outer of this method won't be commited
        self.__session.expire_all()
        device = self.__session.query(Device).filter_by(id=d_id).first()
        if device is None:
            self.__raise_dbhelper_exception("Device with id %s couldn't be found" % d_id)
        
        # Use this method rather than cascade deletion (much faster)
        meta = MetaData(bind=DbHelper.__engine)
        t_stats = Table(DeviceStats.__tablename__, meta, autoload=True)
        self.__session.execute(
            t_stats.delete().where(t_stats.c.device_id == d_id)
        )

        # delete sensor history data
        ssens = self.__session.query(Sensor).filter_by(device_id=d_id).all()
        meta = MetaData(bind=DbHelper.__engine)
        t_hist = Table(SensorHistory.__tablename__, meta, autoload=True)
        for sen in ssens:
            self.__session.execute(
                t_hist.delete().where(t_hist.c.sensor_id == sen.id)
            )
        
        self.__session.delete(device)
        try:
            self.__session.commit()
        except Exception as sql_exception:
            self.__raise_dbhelper_exception("SQL exception (commit) : %s" % sql_exception, True)
        return device

####
# stats upgrade
####
    def upgrade_list_old(self):
        return self.__session.query(Device.id, Device.name, DeviceStats.skey).\
                    filter(Device.id==DeviceStats.device_id).\
                    filter(Device.address!=None).\
                    order_by(Device.id).\
                    distinct()

    def upgrade_list_new(self):
        return self.__session.query(Device.id, Device.name, Sensor.name, Sensor.id).\
                     filter(Device.id==Sensor.device_id).\
                     filter(Device.address==None).\
                     order_by(Device.id).\
                     distinct()

    def upgrade_do(self, oid, okey, nid, nsid):
        self.__session.expire_all()
        oldvals = self.__session.query(DeviceStats.id, DeviceStats.value, DeviceStats.timestamp).\
                     filter(DeviceStats.skey==okey).\
                     filter(DeviceStats.device_id ==oid)
        num = 0
        for val in oldvals:
            # add the value
            self.add_sensor_history(nsid, val[1], val[2])
  	    # increment num
            num += 1
        # delete the statas
        meta = MetaData(bind=DbHelper.__engine)
        t_stats = Table(DeviceStats.__tablename__, meta, autoload=True)
        self.__session.execute(
            t_stats.delete().where(and_(t_stats.c.device_id == oid, t_stats.c.skey == okey))
        )
        try:
            self.__session.commit()
        except Exception as sql_exception:
            self.__raise_dbhelper_exception("SQL exception (commit) : %s" % sql_exception, True)
        return num
            
####
# Sensor history
####
    def add_sensor_history(self, sid, value, date):
        self.__session.expire_all()
        sensor = self.__session.query(Sensor).filter_by(id=sid).first()
        if sensor is not None:
            # store the value if requested
            if sensor.history_store:
                # only store stats if the value is different
                if sensor.last_value is not str(value):
                    # handle history_round
                    # reduce device stats
                    if sensor.history_round > 0:
                        last = self.__session.query(SensorHistory) \
                            .filter(SensorHistory.sensor_id == sid) \
                            .order_by(SensorHistory.date.desc()) \
                            .limit(2) \
                            .all()
                        last.reverse()
                        if last and len(last) == 2:
                            delta = abs(float(last[0].value_num) - float(last[1].value_num))
                            if delta < sensor.history_round:
                                delta0 = abs(float(value) - float(last[0].value_num))
                                delta1 = abs(float(value) - float(last[1].value_num))
                                if delta0 < sensor.history_round \
                                        and delta1 < sensor.history_round:
                                    self.__session.query(SensorHistory) \
                                        .filter(SensorHistory.id == last[1].id) \
                                        .delete()
                    # insert new recored in core_sensor_history
                    h = SensorHistory(sensor.id, datetime.datetime.fromtimestamp(date), value)
                    self.__session.add(h)
                    sensor.last_received = date
                    sensor.last_value = ucode(value)
                    self.__session.add(sensor)
                    try:
                        self.__session.commit()
                    except Exception as sql_exception:
                        self.__raise_dbhelper_exception("SQL exception (commit) : %s" % sql_exception, True)
                # handle the max value
                if sensor.history_max > 0:
                    count = self.__session.query(SensorHistory).filter_by(sensor_id=sensor.id).count()
                    if count > sensor.history_max:
                        # delete from sensor_history where id not in (select id from sensor_history order by date desc limit x)
                        tokeep1 = self.__session.query(SensorHistory.id) \
                                .filter(SensorHistory.sensor_id==sensor.id) \
                                .order_by(SensorHistory.date.desc()) \
                                .limit(sensor.history_max) \
                                .subquery()
                        # ugly fix because mysql is not supporting limit in a subquery
                        tokeep2 = self.__session.query(tokeep1).subquery()
                        self.__session.query(SensorHistory) \
                            .filter( \
                                        SensorHistory.sensor_id==sensor.id, \
                                        ~SensorHistory.id.in_(tokeep2) \
                                    ) \
                            .delete(synchronize_session=False)
                        try:
                            self.__session.commit()
                        except Exception as sql_exception:
                            self.__raise_dbhelper_exception("SQL exception (commit) : %s" % sql_exception, True)
                # handle the expire value (days)
                if sensor.history_expire > 0:
                    stamp = datetime.datetime.now() - datetime.timedelta(days=sensor.history_expire)
                    self.__session.query(SensorHistory) \
                        .filter( \
                                    SensorHistory.date<=stamp, \
                                    SensorHistory.sensor_id==sensor.id \
                                ) \
                        .delete(synchronize_session=False)
                    try:
                        self.__session.commit()
                    except Exception as sql_exception:
                        self.__raise_dbhelper_exception("SQL exception (commit) : %s" % sql_exception, True)
        else:
            self.__raise_dbhelper_exception("Can not add history to not existing sensor: %s" % sid, True)             

    def list_sensor_history(self, sid, num=None):
        if num is None:
            return self.__session.query(SensorHistory).filter(SensorHistory.sensor_id==sid).all()
        else:
            return self.__session.query(SensorHistory).filter(SensorHistory.sensor_id==sid).limit(num).all()
            
    def list_sensor_history_between(self, sid, frm, to=None):
        if to:
            if to < frm:
                self.__raise_dbhelper_exception("'end_date' can't be prior to 'start_date'")
        else:
            to = int(time.time())
        return self.__session.query(SensorHistory
                  ).filter(SensorHistory.sensor_id==sid
                  ).filter(SensorHistory.date>=_datetime_string_from_tstamp(frm)
                  ).filter(SensorHistory.date<=_datetime_string_from_tstamp(to)
                  ).order_by(sqlalchemy.asc(SensorHistory.date)
                  ).all()
       
    def list_sensor_history_filter(self, sid, frm, to, step_used, function_used):
        if not frm:
            self.__raise_dbhelper_exception("You have to provide a start date")
        if to:
            if to < frm:
                self.__raise_dbhelper_exception("'end_date' can't be prior to 'start_date'")
        else:
            to = int(time.time())
        if function_used is None or function_used.lower() not in ('min', 'max', 'avg'):
            self.__raise_dbhelper_exception("'function_used' parameter should be one of : min, max, avg")
        if step_used is None or step_used.lower() not in ('minute', 'hour', 'day', 'week', 'month', 'year'):
            self.__raise_dbhelper_exception("'period' parameter should be one of : minute, hour, day, week, month, year")
        function = {
            'min': func.min(SensorHistory.value_num),
            'max': func.max(SensorHistory.value_num),
            'avg': func.avg(SensorHistory.value_num),
        }
        sql_query = {
            'minute' : {
                # Query for mysql
                # func.week(SensorHistory.date, 3) is equivalent to python's isocalendar()[2] method
                'mysql': self.__session.query(
                            func.year(SensorHistory.date), func.month(SensorHistory.date),
                            func.week(SensorHistory.date, 3), func.day(SensorHistory.date),
                            func.hour(SensorHistory.date), func.minute(SensorHistory.date),
                            function[function_used]
                        ).group_by(
                            func.year(SensorHistory.date), func.month(SensorHistory.date),
                            func.day(SensorHistory.date), func.hour(SensorHistory.date),
                            func.minute(SensorHistory.date)
                        ),
                 'postgresql': self.__session.query(
                            extract('year', SensorHistory.date).label('year_c'), extract('month', SensorHistory.date),
                            extract('week', SensorHistory.date), extract('day', SensorHistory.date),
                            extract('hour', SensorHistory.date), extract('minute', SensorHistory.date),
                            function[function_used]
                        ).group_by(
                            extract('year', SensorHistory.date), extract('month', SensorHistory.date),
                            extract('week', SensorHistory.date), extract('day', SensorHistory.date),
                            extract('hour', SensorHistory.date), extract('minute', SensorHistory.date)
                        ).order_by(
                            sqlalchemy.asc('year_c')
                        )
            },
            'hour' : {
                'mysql': self.__session.query(
                            func.year(SensorHistory.date), func.month(SensorHistory.date),
                            func.week(SensorHistory.date, 3), func.day(SensorHistory.date),
                            func.hour(SensorHistory.date), function[function_used]
                        ).group_by(
                            func.year(SensorHistory.date), func.month(SensorHistory.date),
                            func.day(SensorHistory.date), func.hour(SensorHistory.date)
                        ),
                'postgresql': self.__session.query(
                            extract('year', SensorHistory.date).label('year_c'), extract('month', SensorHistory.date),
                            extract('week', SensorHistory.date), extract('day', SensorHistory.date),
                            extract('hour', SensorHistory.date),
                            function[function_used]
                        ).group_by(
                            extract('year', SensorHistory.date), extract('month', SensorHistory.date),
                            extract('week', SensorHistory.date), extract('day', SensorHistory.date),
                            extract('hour', SensorHistory.date)
                        ).order_by(
                            sqlalchemy.asc('year_c')
                        )
            },
            'day' : {
                'mysql': self.__session.query(
                            func.year(SensorHistory.date), func.month(SensorHistory.date),
                            func.week(SensorHistory.date, 3), func.day(SensorHistory.date),
                                      function[function_used]
                        ).group_by(
                            func.year(SensorHistory.date), func.month(SensorHistory.date),
                            func.day(SensorHistory.date)
                        ),
                'postgresql': self.__session.query(
                            extract('year', SensorHistory.date).label('year_c'), extract('month', SensorHistory.date),
                            extract('week', SensorHistory.date), extract('day', SensorHistory.date),
                            function[function_used]
                        ).group_by(
                            extract('year', SensorHistory.date), extract('month', SensorHistory.date),
                            extract('week', SensorHistory.date), extract('day', SensorHistory.date)
                        ).order_by(
                            sqlalchemy.asc('year_c')
                        )
            },
            'week' : {
                'mysql': self.__session.query(
                            func.year(SensorHistory.date), func.week(SensorHistory.date, 1), function[function_used]
                        ).group_by(
                            func.year(SensorHistory.date), func.week(SensorHistory.date, 1)
                        ),
                'postgresql': self.__session.query(
                            extract('year', SensorHistory.date).label('year_c'), extract('week', SensorHistory.date),
                            function[function_used]
                        ).group_by(
                            extract('year', SensorHistory.date).label('year_c'), extract('week', SensorHistory.date)
                        ).order_by(
                            sqlalchemy.asc('year_c')
                        )
            },
            'year' : {
                'mysql': self.__session.query(
                            func.year(SensorHistory.date), function[function_used]
                        ).group_by(
                            func.year(SensorHistory.date)
                        ),
                'postgresql': self.__session.query(
                            extract('year', SensorHistory.date).label('year_c'), function[function_used]
                        ).group_by(
                            extract('year', SensorHistory.date)
                        ).order_by(
                            sqlalchemy.asc('year_c')
                        )
            },
            'global' : self.__session.query(
                            function['min'], function['max'], function['avg']
                        )
        }
        if self.get_db_type() in ('mysql', 'postgresql'):
            cond_min = "date >= '" + _datetime_string_from_tstamp(frm) + "'"
            cond_max = "date < '" + _datetime_string_from_tstamp(to) + "'"
            query = sql_query[step_used][self.get_db_type()]
            query = query.filter_by(sensor_id=sid
                        ).filter(cond_min
                        ).filter(cond_max)
            results_global = sql_query['global'].filter_by(sensor_id=sid
                                               ).filter(cond_min
                                               ).filter(cond_max
                                               ).first()
            return {
                'values': query.all(),
                'global_values': {
                    'min': results_global[0],
                    'max': results_global[1],
                    'avg': results_global[2]
                }
            }


####
# User accounts
####
    def list_user_accounts(self):
        """Return a list of all accounts

        @return a list of UserAccount objects

        """
        list_sa = self.__session.query(UserAccount).all()
        return list_sa

    def get_user_account(self, a_id):
        """Return user account information from id

        @param a_id : account id
        @return a UserAccount object

        """
        user_acc = self.__session.query(UserAccount).filter_by(id=a_id).first()
        return user_acc

    def get_user_account_by_login(self, a_login):
        """Return user account information from login

        @param a_login : login
        @return a UserAccount object

        """
        return self.__session.query(
                            UserAccount
                        ).filter_by(login=ucode(a_login)
                        ).first()

    def get_user_account_by_person(self, p_id):
        """Return a user account associated to a person, if existing

        @param p_id : The person id
        @return a UserAccount object

        """
        return self.__session.query(
                        UserAccount
                    ).filter_by(person_id=p_id
                    ).first()

    def authenticate(self, a_login, a_password):
        """Check if a user account with a_login, a_password exists

        @param a_login : Account login
        @param a_password : Account password (clear)
        @return True or False

        """
        # Make sure previously modified objects outer of this method won't be commited
        self.__session.expire_all()
        user_acc = self.__session.query(
                            UserAccount
                        ).filter_by(login=ucode(a_login)
                        ).first()
        return user_acc is not None and user_acc._UserAccount__password == _make_crypted_password(a_password)

    def add_user_account(self, a_login, a_password, a_person_id, a_is_admin=False, a_skin_used=''):
        """Add a user account

        @param a_login : Account login
        @param a_password : Account clear text password (will be hashed in sha256)
        @param a_person_id : id of the person associated to the account
        @param a_is_admin : True if it is an admin account, False otherwise (optional, default=False)
        @return the new UserAccount object or raise a DbHelperException if it already exists

        """
        # Make sure previously modified objects outer of this method won't be commited
        self.__session.expire_all()
        user_account = self.__session.query(
                                UserAccount
                            ).filter_by(login=ucode(a_login)
                            ).first()
        if user_account is not None:
            self.__raise_dbhelper_exception("Error %s login already exists" % a_login)
        person = self.__session.query(Person).filter_by(id=a_person_id).first()
        if person is None:
            self.__raise_dbhelper_exception("Person id '%s' does not exist" % a_person_id)
        user_account = UserAccount(login=a_login, password=_make_crypted_password(a_password),
                                   person_id=a_person_id, is_admin=a_is_admin, skin_used=a_skin_used)
        self.__session.add(user_account)
        try:
            self.__session.commit()
        except Exception as sql_exception:
            self.__raise_dbhelper_exception("SQL exception (commit) : %s" % sql_exception, True)
        return user_account

    def add_user_account_with_person(self, a_login, a_password, a_person_first_name, a_person_last_name,
                                     a_person_birthdate=None, a_is_admin=False, a_skin_used=''):
        """Add a user account and a person

        @param a_login : Account login
        @param a_password : Account clear text password (will be hashed in sha256)
        @param a_person_first_name : first name of the person associated to the account
        @param a_person_last_name : last name of the person associated to the account
        @param a_person_birthdate : birthdate of the person associated to the account, optional
        @param a_is_admin : True if it is an admin account, False otherwise (optional, default=False)
        @param a_skin_used : name of the skin choosen by the user (optional, default='skins/default')
        @return the new UserAccount object or raise a DbHelperException if it already exists

        """
        self.__session.expire_all()
        person = self.add_person(a_person_first_name, a_person_last_name, a_person_birthdate)
        return self.add_user_account(a_login, a_password, person.id, a_is_admin, a_skin_used)

    def update_user_account(self, a_id, a_new_login=None, a_person_id=None, a_is_admin=None, a_skin_used=None):
        """Update a user account

        @param a_id : Account id to be updated
        @param a_new_login : The new login (optional)
        @param a_person_id : id of the person associated to the account
        @param a_is_admin : True if it is an admin account, False otherwise (optional)
        @param a_skin_used : name of the skin choosen by the user (optional, default='skins/default')
        @return a UserAccount object

        """
        # Make sure previously modified objects outer of this method won't be commited
        self.__session.expire_all()
        user_acc = self.__session.query(UserAccount).filter_by(id=a_id).first()
        if user_acc is None:
            self.__raise_dbhelper_exception("UserAccount with id %s couldn't be found" % a_id)
        if a_new_login is not None:
            user_acc.login = ucode(a_new_login)
        if a_person_id is not None:
            person = self.__session.query(Person).filter_by(id=a_person_id).first()
            if person is None:
                self.__raise_dbhelper_exception("Person id '%s' does not exist" % a_person_id)
            user_acc.person_id = a_person_id
        if a_is_admin is not None:
            user_acc.is_admin = a_is_admin
        if a_skin_used is not None:
            user_acc.skin_used = ucode(a_skin_used)
        self.__session.add(user_acc)
        try:
            self.__session.commit()
        except Exception as sql_exception:
            self.__raise_dbhelper_exception("SQL exception (commit) : %s" % sql_exception, True)
        return user_acc

    def update_user_account_with_person(self, a_id, a_login=None, p_first_name=None, p_last_name=None, p_birthdate=None,
                                        a_is_admin=None, a_skin_used=None):
        """Update a user account a person information

        @param a_id : Account id to be updated
        @param a_login : The new login (optional)
        @param p_first_name : first name of the person associated to the account, optional
        @param p_last_name : last name of the person associated to the account, optional
        @param p_birthdate : birthdate of the person associated to the account, optional
        @param a_is_admin : True if it is an admin account, False otherwise, optional
        @param a_skin_used : name of the skin choosen by the user (optional, default='skins/default')
        @return a UserAccount object

        """
        self.__session.expire_all()
        user_acc = self.update_user_account(a_id, a_login, None, a_is_admin, a_skin_used)
        # Make sure previously modified objects outer of this method won't be commited
        self.__session.expire_all()
        person = user_acc.person
        if p_first_name is not None:
            person.first_name = ucode(p_first_name)
        if p_last_name is not None:
            person.last_name = ucode(p_last_name)
        if p_birthdate is not None:
            person.birthdate = p_birthdate
        self.__session.add(person)
        try:
            self.__session.commit()
        except Exception as sql_exception:
            self.__raise_dbhelper_exception("SQL exception (commit) : %s" % sql_exception, True)
        return user_acc

    def change_password(self, a_id, a_old_password, a_new_password):
        """Change the password

        @param a_id : account id
        @param a_old_password : the password to change (the old one, in clear text)
        @param a_new_password : the new password, in clear text (will be hashed in sha256)
        @return True if the password could be changed, False otherwise (login or old_password is wrong)

        """
        # Make sure previously modified objects outer of this method won't be commited
        self.__session.expire_all()
        user_acc = self.__session.query(UserAccount).filter_by(id=a_id).first()
        if user_acc is not None:
            old_pass = ucode(_make_crypted_password(a_old_password))
            if user_acc._UserAccount__password != old_pass:
                return False
        else:
            return False
        user_acc.set_password(ucode(_make_crypted_password(a_new_password)))
        self.__session.add(user_acc)
        try:
            self.__session.commit()
        except Exception as sql_exception:
            self.__raise_dbhelper_exception("SQL exception (commit) : %s" % sql_exception, True)
        return True

    def add_default_user_account(self):
        """Add a default user account (login = admin, password = domogik, is_admin = True)
        if there isn't already one

        @return a UserAccount object

        """
        self.__session.expire_all()
        #self.__session.expire_all()

        default_person_fname = "Admin"
        default_person_lname = "Admin"
        default_user_account_login = "admin"
        if self.__session.query(UserAccount).count() > 0:
            return None
        person = self.add_person(p_first_name=default_person_fname, p_last_name=default_person_lname, 
                                 p_birthdate=datetime.date(1900, 1, 1))
        user_account = self.add_user_account(a_login=default_user_account_login, a_password='123', a_person_id=person.id, 
                                     a_is_admin=True)
        #try:
        #    self.__session.commit()
        #except Exception as sql_exception:
        #    self.__raise_dbhelper_exception("SQL exception (commit) : %s" % sql_exception, True)
        return user_account

    def del_user_account(self, a_id):
        """Delete a user account

        @param a_id : account id
        @return the deleted UserAccount object

        """
        # Make sure previously modified objects outer of this method won't be commited
        self.__session.expire_all()
        user_account = self.__session.query(UserAccount).filter_by(id=a_id).first()
        if user_account:
            self.__session.delete(user_account)
            try:
                self.__session.commit()
            except Exception as sql_exception:
                self.__raise_dbhelper_exception("SQL exception (commit) : %s" % sql_exception, True)
            return user_account
        else:
            self.__raise_dbhelper_exception("Couldn't delete user account with id %s : it doesn't exist" % a_id)

####
# Persons
####
    def list_persons(self):
        """Return the list of all persons

        @return a list of Person objects

        """
        return self.__session.query(Person).all()

    def get_person(self, p_id):
        """Return person information

        @param p_id : person id
        @return a Person object

        """
        return self.__session.query(Person).filter_by(id=p_id).first()

    def add_person(self, p_first_name, p_last_name, p_birthdate=None):
        """Add a person

        @param p_first_name     : first name
        @param p_last_name      : last name
        @param p_birthdate      : birthdate, optional
        @param p_user_account   : Person account on the user (optional)
        @return the new Person object

        """
        # Make sure previously modified objects outer of this method won't be commited
        person = Person(first_name=p_first_name, last_name=p_last_name, birthdate=p_birthdate)
        self.__session.add(person)
        try:
            self.__session.commit()
        except Exception as sql_exception:
            self.__raise_dbhelper_exception("SQL exception (commit) : %s" % sql_exception, True)
        return person

    def update_person(self, p_id, p_first_name=None, p_last_name=None, p_birthdate=None):
        """Update a person

        @param p_id             : person id to be updated
        @param p_first_name     : first name (optional)
        @param p_last_name      : last name (optional)
        @param p_birthdate      : birthdate (optional)
        @return a Person object

        """
        # Make sure previously modified objects outer of this method won't be commited
        person = self.__session.query(Person).filter_by(id=p_id).first()
        if person is None:
            self.__raise_dbhelper_exception("Person with id %s couldn't be found" % p_id)
        if p_first_name is not None:
            person.first_name = ucode(p_first_name)
        if p_last_name is not None:
            person.last_name = ucode(p_last_name)
        if p_birthdate is not None:
            if p_birthdate == '':
                p_birthdate = None
            person.birthdate = p_birthdate
        self.__session.add(person)
        try:
            self.__session.commit()
        except Exception as sql_exception:
            self.__raise_dbhelper_exception("SQL exception (commit) : %s" % sql_exception, True)
        return person

    def del_person(self, p_id):
        """Delete a person and the associated user account if it exists

        @param p_id : person account id
        @return the deleted Person object

        """
        # Make sure previously modified objects outer of this method won't be commited
        self.__session.expire_all()
        person = self.__session.query(Person).filter_by(id=p_id).first()
        if person is not None:
            self.__session.delete(person)
            try:
                self.__session.commit()
            except Exception as sql_exception:
                self.__raise_dbhelper_exception("SQL exception (commit) : %s" % sql_exception, True)
            return person
        else:
            self.__raise_dbhelper_exception("Couldn't delete person with id %s : it doesn't exist" % p_id)

###################
# sensor
###################
    def get_all_sensor(self):
        return self.__session.query(Sensor).all()

    def get_sensor(self, id):
        return self.__session.query(Sensor).filter_by(id=id).first()

    def get_sensor_by_device_id(self, did):
        return self.__session.query(Sensor).filter_by(device_id=did).all()

    def update_sensor(self, sid, history_round=None, \
            history_store=None, history_max=None, \
            history_expire=None):
        sensor = self.__session.query(Sensor).filter_by(id=sid).first()
        if sensor is None:
            self.__raise_dbhelper_exception("Sensor with id %s couldn't be found" % sid)
        if history_round is not None:
            sensor.history_round = history_round
        if history_max is not None:
            sensor.history_max = history_max
        if history_store is not None:
            sensor.history_store = history_store
        if history_expire is not None:
            sensor.history_expire = history_expire
        self.__session.add(sensor)
        try:
            self.__session.commit()
        except Exception as sql_exception:
            self.__raise_dbhelper_exception("SQL exception (commit) : %s" % sql_exception, True)
        return sensor



###################
# command
###################
    def get_all_command(self):
        return self.__session.query(Command).all()
    
    def get_command(self, id):
        return self.__session.query(Command).filter_by(id=id).first()
    
    def get_command_by_device_id(self, d_id):
        return self.__session.query(Command).filter_by(device_id=d_id).all()

    def add_command(self, device_id, name, reference, return_confirmation):
        self.__session.expire_all()
        cmd = Command(name=name, device_id=device_id, reference=reference, return_confirmation=return_confirmation)
        self.__session.add(cmd)
        try:
            self.__session.commit()
        except Exception as sql_exception:
            self.__raise_dbhelper_exception("SQL exception (commit) : %s" % sql_exception, True)
        return cmd

###################
# commandParam
###################
    def add_commandparam(self, cmd_id, key, dtype, conversion): 
        self.__session.expire_all()
        p = CommandParam(cmd_id=cmd_id, key=key, data_type=dtype, conversion=conversion)
        self.__session.add(p)
        try:
            self.__session.commit()
        except Exception as sql_exception:
            self.__raise_dbhelper_exception("SQL exception (commit) : %s" % sql_exception, True)
        return p

###################
# xplcommand
###################
    def get_all_xpl_command(self):
        return self.__session.query(XplCommand).all()
    
    def get_xpl_command(self, p_id):
        return self.__session.query(XplCommand).filter_by(id=p_id).first()

    def get_xpl_command_by_device_id(self, d_id):
        return self.__session.query(XplCommand).filter_by(device_id=d_id).all()

    def add_xpl_command(self, cmd_id, name, schema, device_id, stat_id, json_id):
        self.__session.expire_all()
        cmd = XplCommand(cmd_id=cmd_id, name=name, schema=schema, device_id=device_id, stat_id=stat_id, json_id=json_id)
        self.__session.add(cmd)
        try:
            self.__session.commit()
        except Exception as sql_exception:
            self.__raise_dbhelper_exception("SQL exception (commit) : %s" % sql_exception, True)
        return cmd

    def del_xpl_command(self, id):
        self.__session.expire_all()
        cmd = self.__session.query(XplCommand).filter_by(id=id).first()
        if cmd is not None:
            self.__session.delete(cmd)
            try:
                self.__session.commit()
            except Exception as sql_exception:
                self.__raise_dbhelper_exception("SQL exception (commit) : %s" % sql_exception, True)
            return cmd
        else:
            self.__raise_dbhelper_exception("Couldn't delete xpl-command with id %s : it doesn't exist" % id)

    def update_xpl_command(self, id, cmd_id=None, name=None, schema=None, device_id=None, stat_id=None):
        """Update a xpl_stat
        """
        # Make sure previously modified objects outer of this method won't be commited
        self.__session.expire_all()
        cmd = self.__session.query(XplCommand).filter_by(id=id).first()
        if cmd is None:
            self.__raise_dbhelper_exception("XplCommand with id %s couldn't be found" % id)
        if cmd_id is not None:
            cmd.cmd_id = cmd_id
        if schema is not None:
            cmd.schema = ucode(schema)
        if device_id is not None:
            cmd.device_id = device_id
        if stat_id is not None:
            cmd.stat_id = stat_id
        if name is not None:
            cmd.name = name
        self.__session.add(cmd)
        try:
            self.__session.commit()
        except Exception as sql_exception:
            self.__raise_dbhelper_exception("SQL exception (commit) : %s" % sql_exception, True)
        return cmd


###################
# xplstat
###################
    def get_all_xpl_stat(self):
        return self.__session.query(XplStat).all()

    def get_xpl_stat(self, p_id):
        return self.__session.query(XplStat).filter_by(id=p_id).first()
    
    def get_xpl_stat_by_device_id(self, d_id):
        return self.__session.query(XplStat).filter_by(device_id=d_id).all()

    def add_xpl_stat(self, name, schema, device_id, json_id):
        self.__session.expire_all()
        stat = XplStat(name=name, schema=schema, device_id=device_id, json_id=json_id)
        self.__session.add(stat)
        try:
            self.__session.commit()
        except Exception as sql_exception:
            self.__raise_dbhelper_exception("SQL exception (commit) : %s" % sql_exception, True)
        return stat

    def del_xpl_stat(self, id):
        self.__session.expire_all()
        stat = self.__session.query(XplStat).filter_by(id=id).first()
        if stat is not None:
            self.__session.delete(stat)
            try:
                self.__session.commit()
            except Exception as sql_exception:
                self.__raise_dbhelper_exception("SQL exception (commit) : %s" % sql_exception, True)
            return stat
        else:
            self.__raise_dbhelper_exception("Couldn't delete xpl-stat with id %s : it doesn't exist" % id)
    
    def update_xpl_stat(self, id, name=None, schema=None, device_id=None):
        # Make sure previously modified objects outer of this method won't be commited
        self.__session.expire_all()
        stat = self.__session.query(XplStat).filter_by(id=id).first()
        if stat is None:
            self.__raise_dbhelper_exception("XplStat with id %s couldn't be found" % id)
        if schema is not None:
            stat.schema = ucode(schema)
        if device_id is not None:
            stat.device_id = device_id
        if name is not None:
            stat.name = name
        self.__session.add(stat)
        try:
            self.__session.commit()
            param = XplCommandParam(cmd_id=cmd_id, key=key, value=value)
            self.__session.add(param)
            self.__session.commit()
        except Exception as sql_exception:
            self.__raise_dbhelper_exception("SQL exception (commit) : %s" % sql_exception, True)
        return param

###################
# XplCommandParam
###################
    def add_xpl_command_param(self, cmd_id, key, value):
        self.__session.expire_all()
        param = XplCommandParam(cmd_id=cmd_id, key=key, value=value)
        self.__session.add(param)
        try:
            self.__session.commit()
        except Exception as sql_exception:
            self.__raise_dbhelper_exception("SQL exception (commit) : %s" % sql_exception, True)
        return param

    def update_xpl_command_param(self, cmd_id, key, value=None):
        self.__session.expire_all()
        param = self.__session.query(XplCommandParam).filter_by(xplcmd_id=cmd_id).filter_by(key=key).first()
        if param is None:
            self.__raise_dbhelper_exception("XplCommandParam with id %s and key %s couldn't be found" % (cmd_id, key))
        if value is not None:
            param.value = ucode(value)
        self.__session.add(param)
        try:
            self.__session.commit()
        except Exception as sql_exception:
            self.__raise_dbhelper_exception("SQL exception (commit) : %s" % sql_exception, True)
        return param

    def del_xpl_command_param(self, id, key):
        self.__session.expire_all()
        param = self.__session.query(XplCommandParam).filter_by(xplcmd_id=id).filter_by(key=key).first()
        if param is not None:
            self.__session.delete(param)
            try:
                self.__session.commit()
            except Exception as sql_exception:
                self.__raise_dbhelper_exception("SQL exception (commit) : %s" % sql_exception, True)
            return param
        else:
            self.__raise_dbhelper_exception("Couldn't delete xpl-command-param with id %s : it doesn't exist" % id)

###################
# XplStatParam
###################
    def get_xpl_stat_param_by_sensor(self, sensor_id):
        return self.__session.query(XplStatParam).filter_by(sensor_id=sensor_id).first()

    def add_xpl_stat_param(self, statid, key, value, static, ignore_values=None, type=None):
        self.__session.expire_all()
        param = XplStatParam(xplstat_id=statid, key=key, value=value, static=static, sensor_id=None, ignore_values=ignore_values, type=type)
        self.__session.add(param)
        try:
            self.__session.commit()
        except Exception as sql_exception:
            self.__raise_dbhelper_exception("SQL exception (commit) : %s" % sql_exception, True)
        return param

    def update_xpl_stat_param(self, stat_id, key, value=None, static=None, ignore_values=None, type=None):
        self.__session.expire_all()
        param = self.__session.query(XplStatParam).filter_by(xplstat_id=stat_id).filter_by(key=key).first()
        if param is None:
            self.__raise_dbhelper_exception("XplStatParam with id %s couldn't be found" % id)
        if value is not None:
            param.value = ucode(value)
        if static is not None:
            param.static = static
        if ignore_values is not None:
            param.ignore_values = ignore_values
        if type is not None:
            param.type = type
        self.__session.add(param)
        try:
            self.__session.commit()
        except Exception as sql_exception:
            self.__raise_dbhelper_exception("SQL exception (commit) : %s" % sql_exception, True)
        return param

    def del_xpl_stat_param(self, stat_id, key):
        self.__session.expire_all()
        param = self.__session.query(XplStatParam).filter_by(xplstat_id=stat_id).filter_by(key=key).first()
        if param is not None:
            self.__session.delete(param)
            try:
                self.__session.commit()
            except Exception as sql_exception:
                self.__raise_dbhelper_exception("SQL exception (commit) : %s" % sql_exception, True)
            return param
        else:
            self.__raise_dbhelper_exception("Couldn't delete xpl-stat-param with id %s : it doesn't exist" % id)
         
###################
# Scenario
###################
    def list_scenario(self):
        return self.__session.query(Scenario).all()

    def get_scenario(self, s_id):
        return self.__session.query(Scenario).filter_by(id=s_id).first()

    def get_scenario_by_name(self, s_name):
        return self.__session.query(Scenario).filter(Scenario.name==s_name).first()

    def add_scenario(self, name, json):
        self.__session.expire_all()
        scenario = Scenario(name=name, json=json)
        self.__session.add(scenario)
        try:
            self.__session.commit()
        except Exception as sql_exception:
            self.__raise_dbhelper_exception("SQL exception (commit) : %s" % sql_exception, True)
        return scenario

    def update_scenario(self, s_id, name=None, json=None):
        self.__session.expire_all()
        scenario = self.__session.query(Scenario).filter_by(id=s_id).first()
        if scenario is None:
            self.__raise_dbhelper_exception("Scenario with id %s couldn't be found" % s_id)
        if name is not None:
            scenario.name = ucode(name)
        if json is not None:
            scenario.json = ucode(json)
        self.__session.add(scenario)
        try:
            self.__session.commit()
        except Exception as sql_exception:
            self.__raise_dbhelper_exception("SQL exception (commit) : %s" % sql_exception, True)
        return scenario

    def del_scenario(self, s_id):
        self.__session.expire_all()
        scenario = self.__session.query(Scenario).filter_by(id=s_id).first()
        if scenario is not None:
            self.__session.delete(scenario)
            try:
                self.__session.commit()
            except Exception as sql_exception:
                self.__raise_dbhelper_exception("SQL exception (commit) : %s" % sql_exception, True)
            return scenario
        else:
            self.__raise_dbhelper_exception("Couldn't delete scenario with id %s : it doesn't exist" % s_id)

###################
# ScenarioUUID
###################
    def list_scenario_uuid(self):
        return self.__session.query(ScenarioUUID).all()

    def get_scenario_uuid(self, u_id):
        return self.__session.query(ScenarioUUID).filter_by(id=u_id).first()

    def add_scenario_uuid(self, s_id, uuid, key, is_test):
        self.__session.expire_all()
        scenariouuid = ScenarioUUID(s_id=s_id, uuid=uuid, key=key, is_test=is_test)
        self.__session.add(scenariouuid)
        try:
            self.__session.commit()
        except Exception as sql_exception:
            self.__raise_dbhelper_exception("SQL exception (commit) : %s" % sql_exception, True)
        return scenariouuid

    def update_scenario_uuid(self, u_id, uuid=None, key=None, is_test=None):
        self.__session.expire_all()
        scenariouuid = self.__session.query(ScenarioUUID).filter_by(id=u_id).first()
        if scenariouuid is None:
            self.__raise_dbhelper_exception("ScenarioUUID with id %s couldn't be found" % u_id)
        if uuid is not None:
            scenariouuid.uuid = ucode(uuid)
        if key is not None:
            scenariouuid.key = ucode(key)
        if is_test is not None:
            scenariouuid.is_test = is_test
        self.__session.add(scenariouuid)
        try:
            self.__session.commit()
        except Exception as sql_exception:
            self.__raise_dbhelper_exception("SQL exception (commit) : %s" % sql_exception, True)
        return scenariouuid

    def del_scenario_uuid(self, u_id):
        self.__session.expire_all()
        scenariouuid = self.__session.query(ScenarioUUID).filter_by(id=u_id).first()
        if scenariouuid is not None:
            self.__session.delete(scenariouuid)
            try:
                self.__session.commit()
            except Exception as sql_exception:
                self.__raise_dbhelper_exception("SQL exception (commit) : %s" % sql_exception, True)
            return scenariouuid
        else:
            self.__raise_dbhelper_exception("Couldn't delete scenario with id %s : it doesn't exist" % s_id)

###################
# Device Config
###################
    def add_device_param(self, d_id, key, value, type): 
        self.__session.expire_all()
        config = DeviceParam(device_id=d_id, key=key, value=value, type=type)
        self.__session.add(config)
        try:
            self.__session.commit()
        except Exception as sql_exception:
            self.__raise_dbhelper_exception("SQL exception (commit) : %s" % sql_exception, True)
        return config

    def udpate_device_param(self, dc_id, key=None, value=None):
        self.__session.expire_all()
        config = self.__session.query(DeviceParam).filter_by(id=dc_id).first()
        if config is None:
            self.__raise_dbhelper_exception("ScenarioUUID with id %s couldn't be found" % u_id)
        if key is not None:
            config.key = ucode(key)
        if value is not None:
            config.value = ucode(value)
        self.__session.add(config)
        try:
            self.__session.commit()
        except Exception as sql_exception:
            self.__raise_dbhelper_exception("SQL exception (commit) : %s" % sql_exception, True)
        return config

###################
# helper functions
###################
    def __raise_dbhelper_exception(self, error_msg, with_rollback=False):
        """Raise a DbHelperException and log it

        @param error_msg : error message
        @param with_rollback : True if a rollback should be done (default is set to False)

        """
        self.log.error(error_msg)
        if with_rollback:
            self.__session.rollback()
        raise DbHelperException(error_msg)

