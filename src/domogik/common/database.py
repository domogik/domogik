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
from types import DictType

import json
import sqlalchemy
from sqlalchemy import Table, MetaData
from sqlalchemy.sql.expression import func, extract
from sqlalchemy.orm import sessionmaker,scoped_session
from sqlalchemy.orm.exc import MultipleResultsFound, NoResultFound
from sqlalchemy.pool import QueuePool

from domogik.common.utils import ucode
from domogik.common import logger
from domogik.common.configloader import Loader
from domogik.common.sql_schema import (
        ACTUATOR_VALUE_TYPE_LIST, Device, DeviceFeature, DeviceFeatureModel,
        DeviceUsage, DeviceStats,
        DeviceTechnology, PluginConfig, DeviceType, Person,
        UserAccount, SENSOR_VALUE_TYPE_LIST
)


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
        
        if config[0]['log_level'] == 'debug':
            logger.Logger('sqlalchemy.engine', domogik_prefix=False, use_filename='sqlalchemy')
            logger.Logger('sqlalchemy.pool', domogik_prefix=False, use_filename='sqlalchemy')
            logger.Logger('sqlalchemy.orm', domogik_prefix=False, use_filename='sqlalchemy')

        url = self.get_url_connection_string()
        if use_test_db:
            url = '%s_test' % url
        # Connecting to the database
        if DbHelper.__engine == None:
            if engine != None:
                DbHelper.__engine = engine
            else:
                DbHelper.__engine = sqlalchemy.create_engine(url, echo = echo_output, encoding='utf8', 
                                                             pool_recycle=7200, pool_size=20, max_overflow=10)
        if DbHelper.__session_object == None:
            DbHelper.__session_object = sessionmaker(bind=DbHelper.__engine, autoflush=True)
        self.__session = DbHelper.__session_object()

    def get_engine(self):
        """Return the existing engine or None if not set
        @return self.__engine

        """
        return DbHelper.__engine

    def __del__(self):
        self.__session.close()

    def __rollback(self):
        """Issue a rollback to a SQL transaction (for dev purposes only)

        """
        self.__session.rollback()

    def get_url_connection_string(self):
        """Get url connection string to the database reading the configuration file"""
        url = "%s://" % self.__db_config['db_type']
        if self.__db_config['db_port'] != '':
            url = "%s%s:%s@%s:%s/%s" % (url, self.__db_config['db_user'], self.__db_config['db_password'],
                                        self.__db_config['db_host'], self.__db_config['db_port'], self.__db_config['db_name'])
        else:
            url = "%s%s:%s@%s/%s" % (url, self.__db_config['db_user'], self.__db_config['db_password'],
                                     self.__db_config['db_host'], self.__db_config['db_name'])
        return url
    
    def get_db_user(self):
        return self.__db_config['db_user']

    def get_db_password(self):
        return self.__db_config['db_password']
    
    def get_db_name(self):
        return self.__db_config['db_name']

    def is_db_type_mysql(self):
        return self.__db_config['db_type'].lower() == 'mysql'

    def get_db_type(self):
        """Return DB type which is currently used (mysql, postgresql)"""
        return self.__db_config['db_type'].lower()

####
# Device usage
####
    def list_device_usages(self):
        """Return a list of device usages

        @return a list of DeviceUsage objects

        """
        return self.__session.query(DeviceUsage).all()

    def get_device_usage_by_name(self, du_name,):
        """Return information about a device usage

        @param du_name : The device usage name
        @return a DeviceUsage object

        """
        return self.__session.query(
                            DeviceUsage
                    ).filter(func.lower(DeviceUsage.name)==ucode(du_name.lower())
                    ).first()

    def add_device_usage(self, du_id, du_name, du_description=None, du_default_options=None):
        """Add a device_usage (temperature, heating, lighting, music, ...)

        @param du_id : device id
        @param du_name : device usage name
        @param du_description : device usage description (optional)
        @param du_default_options : default options (optional)
        @return a DeviceUsage (the newly created one)

        """
        # Make sure previously modified objects outer of this method won't be commited
        self.__session.expire_all()
        du = DeviceUsage(id=ucode(du_id), name=ucode(du_name), description=du_description,
                         default_options=du_default_options)
        self.__session.add(du)
        try:
            self.__session.commit()
        except Exception as sql_exception:
            self.__raise_dbhelper_exception("SQL exception (commit) : %s" % sql_exception, True)
        return du

    def update_device_usage(self, du_id, du_name=None, du_description=None, du_default_options=None):
        """Update a device usage

        @param du_id : device usage id to be updated
        @param du_name : device usage name (optional)
        @param du_description : device usage detailed description (optional)
        @param du_default_options : default options (optional)
        @return a DeviceUsage object

        """
        # Make sure previously modified objects outer of this method won't be commited
        self.__session.expire_all()
        device_usage = self.__session.query(DeviceUsage).filter_by(id=du_id).first()
        if device_usage is None:
            self.__raise_dbhelper_exception("DeviceUsage with id %s couldn't be found" % du_id)
        if du_id is not None:
            device_usage.id = ucode(du_id)
        if du_name is not None:
            device_usage.name = ucode(du_name)
        if du_description is not None:
            if du_description == '': du_description = None
            device_usage.description = ucode(du_description)
        if du_default_options is not None:
            if du_default_options == '': du_default_options = None
            device_usage.default_options = ucode(du_default_options)
        self.__session.add(device_usage)
        try:
            self.__session.commit()
        except Exception as sql_exception:
            self.__raise_dbhelper_exception("SQL exception (commit) : %s" % sql_exception, True)
        return device_usage

    def del_device_usage(self, du_id, cascade_delete=False):
        """Delete a device usage record

        @param dc_id : id of the device usage to delete
        @return the deleted DeviceUsage object

        """
        # Make sure previously modified objects outer of this method won't be commited
        self.__session.expire_all()
        du = self.__session.query(DeviceUsage).filter_by(id=ucode(du_id)).first()
        if du:
            if cascade_delete:
                for device in self.__session.query(Device).filter_by(device_usage_id=ucode(du.id)).all():
                    self.del_device(device.id)
            else:
                device_list = self.__session.query(Device).filter_by(device_usage_id=ucode(du.id)).all()
                if len(device_list) > 0:
                    self.__raise_dbhelper_exception("Couldn't delete device usage %s : there are associated devices" % du_id)

            self.__session.delete(du)
            try:
                self.__session.commit()
            except Exception as sql_exception:
                self.__raise_dbhelper_exception("SQL exception (commit) : %s" % sql_exception, True)
            return du
        else:
            self.__raise_dbhelper_exception("Couldn't delete device usage with id %s : it doesn't exist" % du_id)

####
# Device type
####
    def list_device_types(self):
        """Return a list of device types

        @return a list of DeviceType objects

        """
        return self.__session.query(DeviceType).all()

    def get_device_type_by_name(self, dty_name):
        """Return information about a device type

        @param dty_name : The device type name
        @return a DeviceType object

        """
        return self.__session.query(
                        DeviceType
                    ).filter(func.lower(DeviceType.name)==ucode(dty_name.lower())
                    ).first()
    
    def get_device_type_by_id(self, dty_id):
        """Return information about a device type

        @param dty_id : The device type id
        @return a DeviceType object

        """
        return self.__session.query(
                        DeviceType
                    ).filter(func.lower(DeviceType.id)==ucode(dty_id)
                    ).first()

    def add_device_type(self, dty_id, dty_name, dt_id, dty_description=None):
        """Add a device_type (Switch, Dimmer, WOL...)

        @param dty_id : device type id
        @param dty_name : device type name
        @param dt_id : technology id (x10, plcbus,...)
        @param dty_description : device type description (optional)
        @return a DeviceType (the newly created one)

        """
        # Make sure previously modified objects outer of this method won't be commited
        self.__session.expire_all()
        if not self.__session.query(DeviceTechnology).filter_by(id=dt_id).first():
            self.__raise_dbhelper_exception("Couldn't add device type with technology id %s. It does not exist" % dt_id)
        dty = DeviceType(id=ucode(dty_id), name=ucode(dty_name), description=ucode(dty_description),
                         device_technology_id=dt_id)
        self.__session.add(dty)
        try:
            self.__session.commit()
        except Exception as sql_exception:
            raise DbHelperException("SQL exception (commit) : %s" % sql_exception)
        return dty

    def update_device_type(self, dty_id, dty_name=None, dt_id=None, dty_description=None):
        """Update a device type

        @param dty_id : device type id to be updated
        @param dty_name : device type name (optional)
        @param dt_id : id of the associated technology (optional)
        @param dty_description : device type detailed description (optional)
        @return a DeviceType object

        """
        # Make sure previously modified objects outer of this method won't be commited
        self.__session.expire_all()
        device_type = self.__session.query(DeviceType).filter_by(id=dty_id).first()
        if device_type is None:
            self.__raise_dbhelper_exception("DeviceType with id %s couldn't be found" % dty_id)
        if dty_id is not None:
            device_type.id = ucode(dty_id)
        if dty_name is not None:
            device_type.name = ucode(dty_name)
        if dt_id is not None:
            if not self.__session.query(DeviceTechnology).filter_by(id=dt_id).first():
                self.__raise_dbhelper_exception("Couldn't find technology id %s. It does not exist" % dt_id)
            device_type.device_technology_id = dt_id
        self.__session.add(device_type)
        if dty_description is not None:
            if dty_description == '': dty_description = None
            device_type.description = ucode(dty_description)
        try:
            self.__session.commit()
        except Exception as sql_exception:
            self.__raise_dbhelper_exception("SQL exception (commit) : %s" % sql_exception)
        return device_type

    def del_device_type(self, dty_id, cascade_delete=False):
        """Delete a device type

        @param dty_id : device type id
        @param cascade_delete : if set to True records of binded tables will be deleted (default is False)
        @return the deleted DeviceType object

        """
        # Make sure previously modified objects outer of this method won't be commited
        self.__session.expire_all()
        dty = self.__session.query(DeviceType).filter_by(id=ucode(dty_id)).first()
        if dty:
            if cascade_delete:
                for device in self.__session.query(Device).filter_by(device_type_id=ucode(dty.id)).all():
                    self.del_device(device.id)
                for df in self.__session.query(DeviceFeatureModel).filter_by(device_type_id=ucode(dty.id)).all():
                    if df.feature_type == 'actuator':
                        self.del_actuator_feature_model(df.id)
                    elif df.feature_type == 'sensor':
                        self.del_sensor_feature_model(df.id)
            else:
                device_list = self.__session.query(Device).filter_by(device_type_id=ucode(dty.id)).all()
                if len(device_list) > 0:
                    self.__raise_dbhelper_exception("Couldn't delete device type %s : there are associated device(s)" % dty_id)
                df_list = self.__session.query(DeviceFeatureModel).filter_by(device_type_id=ucode(dty.id)).all()
                if len(df_list) > 0:
                    self.__raise_dbhelper_exception("Couldn't delete device type %s : there are associated device type "
                                               + "feature(s)" % dty_id)
            self.__session.delete(dty)
            try:
                self.__session.commit()
            except Exception as sql_exception:
                self.__raise_dbhelper_exception("SQL exception (commit) : %s" % sql_exception, True)
            return dty
        else:
            self.__raise_dbhelper_exception("Couldn't delete device type with id %s : it doesn't exist" % dty_id)

####
# Device features
####
    def get_device_feature(self, df_device_id, df_device_feature_model_id):
        """Return a device feature

        @param df_device_id : device id
        @param df_device_feature_model_id : id of the device feature model
        @return a DeviceFeature object

        """
        return self.__session.query(
                        DeviceFeature
                    ).filter_by(device_id=df_device_id, device_feature_model_id=df_device_feature_model_id
                    ).first()

    def get_device_feature_by_id(self, df_id):
        """Return a device feature

        @param df_id : device feature id
        @return a DeviceFeature object

        """
        return self.__session.query(DeviceFeature).filter_by(id=df_id).first()

    def list_device_features(self):
        """List device features

        @return a list of DeviceFeature objects

        """
        return self.__session.query(DeviceFeature).all()

    def list_device_features_by_device_id(self, df_device_id):
        """List device features for a device

        @param df_device_id : device id
        @return a list of DeviceFeature objects

        """
        return self.__session.query(DeviceFeature).filter_by(device_id=df_device_id).all()

    def list_device_feature_by_device_id(self, df_device_id):
        """List device features for a given device id

        @param df_device_id : device id
        @return a list of DeviceFeature objects

        """
        return self.__session.query(DeviceFeature).filter_by(device_id=df_device_id).all()

    def list_device_feature_by_device_feature_model_id(self, df_device_feature_model_id):
        """List device features for a given device id

        @param df_device_feature_model_id : device feature model id
        @return a list of DeviceFeature objects

        """
        return self.__session.query(
                        DeviceFeature
                    ).filter_by(device_feature_model_id=df_device_feature_model_id
                    ).all()        

####
# Device feature models
####
    def list_device_feature_models(self):
        """Return a list of models for device type feature

        @return a list of DeviceFeatureModel objects

        """
        return self.__session.query(DeviceFeatureModel).all()

    def list_device_feature_models_by_device_type_id(self, dtf_device_type_id):
        """Return a list of models for device type features (actuator, sensor) knowing the device type id

        @param dtf_device_type_id : device type id
        @return a list of DeviceFeatureModel objects

        """
        return self.__session.query(
                        DeviceFeatureModel
                    ).filter_by(device_type_id=dtf_device_type_id
                    ).all()

    def get_device_feature_model_by_id(self, dtf_id):
        """Return information about a model for a device type feature

        @param dtf_id : model id
        @return a DeviceFeatureModel object

        """
        return self.__session.query(DeviceFeatureModel).filter_by(id=dtf_id).first()

####
# Actuator feature model
####
    def list_actuator_feature_models(self):
        """Return a list of models for actuator features

        @return a list of DeviceFeatureModel objects

        """
        return self.__session.query(
                        DeviceFeatureModel
                    ).filter_by(feature_type=u'actuator'
                    ).all()

    def get_actuator_feature_model_by_id(self, af_id):
        """Return information about a model for an actuator feature

        @param af_id : actuator feature model id
        @return an DeviceFeatureModel object

        """
        return self.__session.query(
                        DeviceFeatureModel
                    ).filter_by(id=ucode(af_id)
                    ).filter_by(feature_type=u'actuator'
                    ).first()

    def add_actuator_feature_model(self, af_id, af_name, af_device_type_id, af_value_type, af_return_confirmation=False,
                                   af_parameters=None, af_stat_key=None):
        """Add a model for an actuator feature

        @param af_id : actuator id
        @param af_name : actuator name
        @param af_device_type_id : device type id
        @param af_value_type : value type the actuator can accept
        @param af_return_confirmation : True if the actuator returns a confirmation after having executed a command, optional (default False)
        @param af_parameters : parameters about the command or the returned data associated to the device, optional
        @param af_stat_key : key reference in the core_device_stats table
        @return a DeviceFeatureModel object (the newly created one)

        """
        # Make sure previously modified objects outer of this method won't be commited
        self.__session.expire_all()
        if af_value_type not in ACTUATOR_VALUE_TYPE_LIST:
            self.__raise_dbhelper_exception("Value type (%s) is not in the allowed item list : %s"
                                       % (af_value_type, ACTUATOR_VALUE_TYPE_LIST))
        if self.__session.query(DeviceType).filter_by(id=af_device_type_id).first() is None:
            self.__raise_dbhelper_exception("Can't add actuator feature : device type id '%s' doesn't exist"
                                       % af_device_type_id)
        device_feature_m = DeviceFeatureModel(id=ucode(af_id), name=ucode(af_name), feature_type=u'actuator',
                                              device_type_id=af_device_type_id, value_type=af_value_type,
                                              return_confirmation=af_return_confirmation,
                                              parameters=af_parameters, stat_key=af_stat_key)
        self.__session.add(device_feature_m)
        try:
            self.__session.commit()
        except Exception as sql_exception:
            self.__raise_dbhelper_exception("SQL exception (commit) : %s" % sql_exception, True)
        return device_feature_m

    def update_actuator_feature_model(self, af_id, af_name=None, af_parameters=None, af_value_type=None,
                                      af_return_confirmation=None, af_stat_key=None):
        """Update a model for an actuator feature

        @param af_id : actuator feature model id
        @param af_name : actuator feature name (Switch, Dimmer, ...), optional
        @param af_parameters : parameters about the command or the returned data associated to the device, optional
        @param af_value_type : value type the actuator can accept, optional
        @param af_return_confirmation : True if the actuator returns a confirmation after having executed a command, optional
        @param af_stat_key : key reference in the core_device_stats table
        @return a DeviceFeatureModel object (the newly updated one)

        """
        # Make sure previously modified objects outer of this method won't be commited
        self.__session.expire_all()
        device_feature_m = self.__session.query(
                                    DeviceFeatureModel
                                ).filter_by(id=ucode(af_id)
                                ).filter_by(feature_type=u'actuator'
                                ).first()
        if device_feature_m is None:
            self.__raise_dbhelper_exception("DeviceFeatureModel with id %s (actuator) couldn't be found - can't update it"
                                       % af_id)
        if af_id is not None:
            device_feature_m.id = ucode(af_id)
        if af_name is not None:
            device_feature_m.name = ucode(af_name)
        if af_parameters is not None:
            if af_parameters == '':
                af_parameters = None
            device_feature_m.parameters = ucode(af_parameters)
        if af_value_type is not None:
            if af_value_type not in ACTUATOR_VALUE_TYPE_LIST:
                self.__raise_dbhelper_exception("Value type (%s) is not in the allowed item list : %s"
                                           % (af_value_type, ACTUATOR_VALUE_TYPE_LIST))
            device_feature_m.value_type = ucode(af_value_type)
        if af_return_confirmation is not None:
            device_feature_m.return_confirmation = af_return_confirmation
        if af_stat_key is not None:
            device_feature_m.stat_key = ucode(af_stat_key)
        self.__session.add(device_feature_m)
        try:
            self.__session.commit()
        except Exception as sql_exception:
            self.__raise_dbhelper_exception("SQL exception (commit) : %s" % sql_exception, True)
        return device_feature_m

    def del_actuator_feature_model(self, afm_id):
        """Delete a model for an actuator feature

        @param afm_id : actuator feature model id
        @return : the deleted object (DeviceFeatureModel)

        """
        # Make sure previously modified objects outer of this method won't be commited
        self.__session.expire_all()
        dfm = self.__session.query(
                        DeviceFeatureModel
                    ).filter_by(id=ucode(afm_id)
                    ).filter_by(feature_type=u'actuator'
                    ).first()
        if not dfm:
            self.__raise_dbhelper_exception("Can't delete device feature model %s (actuator) : it doesn't exist" % afm_id)
        self.__session.delete(dfm)
        try:
            self.__session.commit()
        except Exception as sql_exception:
            self.__raise_dbhelper_exception("SQL exception (commit) : %s" % sql_exception, True)
        return dfm

####
# Sensor feature model
####
    def list_sensor_feature_models(self):
        """Return a list of models for sensor features

        @return a list of DeviceFeatureModel objects

        """
        return self.__session.query(
                        DeviceFeatureModel
                    ).filter_by(feature_type=u'sensor'
                    ).all()

    def get_sensor_feature_model_by_id(self, sf_id):
        """Return information about a model for a sensor feature

        @param sf_id : sensor feature model id
        @return a DeviceFeatureModel object

        """
        return self.__session.query(
                        DeviceFeatureModel
                    ).filter_by(id=ucode(sf_id)
                    ).filter_by(feature_type=u'sensor'
                    ).first()

    def add_sensor_feature_model(self, sf_id, sf_name, sf_device_type_id, sf_value_type, sf_parameters=None,
                                 sf_stat_key=None):
        """Add a model for sensor feature

        @param sf_id : sensor feature id
        @param sf_name : sensor feature name (Thermometer, Voltmeter...)
        @param sf_device_type_id : device type id
        @param sf_value_type : value type the sensor can return
        @param sf_parameters : parameters about the command or the returned data associated to the device, optional
        @param sf_stat_key : key reference in the core_device_stats table
        @return a DeviceFeatureModel object (the newly created one)

        """
        # Make sure previously modified objects outer of this method won't be commited
        self.__session.expire_all()
        if sf_value_type not in SENSOR_VALUE_TYPE_LIST:
            self.__raise_dbhelper_exception("Value type (%s) is not in the allowed item list : %s"
                                       % (sf_value_type, SENSOR_VALUE_TYPE_LIST))
        if self.__session.query(DeviceType).filter_by(id=ucode(sf_device_type_id)).first() is None:
            self.__raise_dbhelper_exception("Can't add sensor : device type id '%s' doesn't exist" % sf_device_type_id)
        device_feature_m = DeviceFeatureModel(id=ucode(sf_id), name=ucode(sf_name), feature_type=u'sensor',
                                              device_type_id=sf_device_type_id, value_type=ucode(sf_value_type),
                                              parameters=ucode(sf_parameters), stat_key=ucode(sf_stat_key))
        self.__session.add(device_feature_m)
        try:
            self.__session.commit()
        except Exception as sql_exception:
            self.__raise_dbhelper_exception("SQL exception (commit) : %s" % sql_exception, True)
        return device_feature_m

    def update_sensor_feature_model(self, sf_id, sf_name=None, sf_parameters=None, sf_value_type=None,
                                    sf_stat_key=None):
        """Update a model for a sensor feature

        @param sf_id : sensor feature model id
        @param sf_name : sensor feature name (Thermometer, Voltmeter...), optional
        @param sf_parameters : parameters about the command or the returned data associated to the device, optional
        @param sf_value_type : value type the sensor can return, optional
        @param sf_stat_key : key reference in the core_device_stats table
        @return a DeviceFeatureModel object (the newly updated one)

        """
        # Make sure previously modified objects outer of this method won't be commited
        self.__session.expire_all()
        device_feature_m = self.__session.query(
                                    DeviceFeatureModel
                                ).filter_by(id=ucode(sf_id)
                                ).filter_by(feature_type=u'sensor'
                                ).first()
        if device_feature_m is None:
            self.__raise_dbhelper_exception("DeviceFeatureModel with id %s couldn't be found - can't update it" % sf_id)
        if sf_id is not None:
            device_feature_m.id = ucode(sf_id)
        if sf_name is not None:
            device_feature_m.name = ucode(sf_name)
        if sf_parameters is not None:
            if sf_parameters == '':
                sf_parameters = None
            device_feature_m.parameters = ucode(sf_parameters)
        if sf_value_type is not None:
            if sf_value_type not in SENSOR_VALUE_TYPE_LIST:
                self.__raise_dbhelper_exception("Value type (%s) is not in the allowed item list : %s"
                                           % (sf_value_type, SENSOR_VALUE_TYPE_LIST))
            device_feature_m.value_type = ucode(sf_value_type)
        if sf_stat_key is not None:
            device_feature_m.stat_key = ucode(sf_stat_key)
        self.__session.add(device_feature_m)
        try:
            self.__session.commit()
        except Exception as sql_exception:
            self.__raise_dbhelper_exception("SQL exception (commit) : %s" % sql_exception, True)
        return device_feature_m

    def del_sensor_feature_model(self, sfm_id):
        """Delete a model for a sensor feature

        @param sfm_id : sensor feature model id
        @return : the deleted object (DeviceFeatureModel)

        """
        # Make sure previously modified objects outer of this method won't be commited
        self.__session.expire_all()
        dfm = self.__session.query(
                        DeviceFeatureModel
                    ).filter_by(id=ucode(sfm_id)
                    ).filter_by(feature_type=u'sensor'
                    ).first()
        if not dfm:
            self.__raise_dbhelper_exception("Can't delete device feature model %s (actuator) : it doesn't exist" % sfm_id)
        self.__session.delete(dfm)
        try:
            self.__session.commit()
        except Exception as sql_exception:
            self.__raise_dbhelper_exception("SQL exception (commit) : %s" % sql_exception, True)
        return dfm

####
# Device technology
####
    def list_device_technologies(self):
        """Return a list of device technologies

        @return a list of DeviceTechnology objects

        """
        return self.__session.query(DeviceTechnology).all()

    def get_device_technology_by_id(self, dt_id):
        """Return information about a device technology

        @param dt_id : the device technology id
        @return a DeviceTechnology object

        """
        return self.__session.query(
                        DeviceTechnology
                    ).filter_by(id=ucode(dt_id)
                    ).first()

    def add_device_technology(self, dt_id, dt_name, dt_description=None):
        """Add a device_technology

        @param dt_id : technology id (ie x10, plcbus, eibknx...) with no spaces / accents or special characters
        @param dt_name : device technology name, one of 'x10', '1wire', 'PLCBus', 'RFXCom', 'IR'
        @param dt_description : extended description of the technology

        """
        # Make sure previously modified objects outer of this method won't be commited
        self.__session.expire_all()
        dt = DeviceTechnology(id=dt_id, name=dt_name, description=dt_description)
        self.__session.add(dt)
        try:
            self.__session.commit()
        except Exception as sql_exception:
            self.__raise_dbhelper_exception("SQL exception (commit) : %s" % sql_exception, True)
        return dt

    def update_device_technology(self, dt_id, dt_name=None, dt_description=None):
        """Update a device technology

        @param dt_id : device technology id to be updated
        @param dt_name : device technology name (optional)
        @param dt_description : device technology detailed description (optional)
        @return a DeviceTechnology object

        """
        # Make sure previously modified objects outer of this method won't be commited
        self.__session.expire_all()
        device_tech = self.__session.query(
                                DeviceTechnology
                            ).filter_by(id=ucode(dt_id)
                            ).first()
        if device_tech is None:
            self.__raise_dbhelper_exception("DeviceTechnology with id %s couldn't be found" % dt_id)
        if dt_name is not None:
            device_tech.name = ucode(dt_name)
        if dt_description is not None:
            if dt_description == '': dt_description = None
            device_tech.description = ucode(dt_description)
        self.__session.add(device_tech)
        try:
            self.__session.commit()
        except Exception as sql_exception:
            self.__raise_dbhelper_exception("SQL exception (commit) : %s" % sql_exception, True)
        return device_tech

    def del_device_technology(self, dt_id, cascade_delete=False):
        """Delete a device technology record

        @param dt_id : id of the device technology to delete
        @param cascade_delete : True if related objects should be deleted, optional default set to False
        @return the deleted DeviceTechnology object

        """
        # Make sure previously modified objects outer of this method won't be commited
        self.__session.expire_all()
        dt = self.__session.query(DeviceTechnology).filter_by(id=ucode(dt_id)).first()
        if dt:
            if cascade_delete:
                for device_type in self.__session.query(DeviceType).filter_by(device_technology_id=ucode(dt.id)).all():
                    self.del_device_type(device_type.id, cascade_delete=True)
                    self.__session.commit()
            else:
                device_type_list = self.__session.query(
                                            DeviceType
                                        ).filter_by(device_technology_id=ucode(dt.id)
                                        ).all()
                if len(device_type_list) > 0:
                    self.__raise_dbhelper_exception("Couldn't delete device technology %s : there are associated device types"
                                               % dt_id)

            self.__session.delete(dt)
            try:
                self.__session.commit()
            except Exception as sql_exception:
                self.__raise_dbhelper_exception("SQL exception (commit) : %s" % sql_exception, True)
            return dt
        else:
            self.__raise_dbhelper_exception("Couldn't delete device technology with id %s : it doesn't exist" % dt_id)

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
        self.log.debug("GPC %s, %s, %s" % (pl_id, pl_hostname, pl_key)) 
        try:
            ret = self.__session.query(
                        PluginConfig
                    ).filter_by(id=ucode(pl_id)
                    ).filter_by(hostname=ucode(pl_hostname)
                    ).filter_by(key=ucode(pl_key)
                    ).first()
            self.log.debug("GPC %s, %s, %s => %s=%s" % (pl_id, pl_hostname, pl_key, ret.key, ret.value)) 
        except:
            self.log.Debug("oups")
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
            self.__raise_dbhelper_exception("SQL exception (commit) : " % sql_exception, True)
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

        @return a list of Device objects

        """
        return self.__session.query(Device).all()

    def get_device(self, d_id):
        """Return a device by its id

        @param d_id : The device id
        @return a Device object

        """
        return self.__session.query(Device).filter_by(id=d_id).first()

    def get_device_by_technology_and_address(self, techno_id, device_address):
        """Return a device by its technology and address

        @param techno_id : technology id
        @param device address : device address
        @return a device object

        """
        device_list = self.__session.query(
                                Device
                            ).filter_by(address=ucode(device_address)
                            ).all()
        if len(device_list) == 0:
            return None
        device = []
        for device in device_list:
            device_type = self.__session.query(
                                    DeviceType
                                ).filter_by(id=device.device_type_id
                                ).first()
            device_tech = self.__session.query(
                                    DeviceTechnology
                                ).filter_by(id=device_type.device_technology_id
                                ).first()
            if device_tech.id.lower() == ucode(techno_id.lower()):
                return device
        return None

    def get_all_devices_of_usage(self, du_id):
        """Return all the devices of a usage

        @param du_id: usage id
        @return a list of Device objects

        """
        return self.__session.query(Device).filter_by(usage_id=du_id).all()

    def add_device(self, d_name, d_address, d_type_id, d_usage_id, d_description=None, d_reference=None):
        """Add a device item

        @param d_name : name of the device
        @param d_address : address (ex : 'A3' for x10/plcbus, '111.111111111' for 1wire)
        @param d_type_id : device type id (x10.Switch, x10.Dimmer, Computer.WOL...)
        @param d_usage_id : usage id (ex. temperature)
        @param d_description : extended device description, optional
        @param d_reference : device reference (ex. AM12 for x10), optional
        @return the new Device object

        """
        # Make sure previously modified objects outer of this method won't be commited
        self.__session.expire_all()
        if not self.__session.query(DeviceType).filter_by(id=d_type_id).first():
            self.__raise_dbhelper_exception("Couldn't add device with device type id %s It does not exist" % d_type_id)
        if not self.__session.query(DeviceUsage).filter_by(id=d_usage_id).first():
            self.__raise_dbhelper_exception("Couldn't add device with device usage id %s It does not exist" % d_usage_id)
        if self.__session.query(Device).filter(Device.address==d_address).filter(Device.device_type_id==d_type_id).count() != 0:
            self.__raise_dbhelper_exception("Couldn't add device, same device with adress %s and type %s already exists" % (d_address,d_type_id))
        device = Device(name=d_name, address=d_address, description=d_description, reference=d_reference,
                        device_type_id=d_type_id, device_usage_id=d_usage_id)
        self.__session.add(device)
        try:
            self.__session.commit()
            # Look up for device feature models according to the device type and create corresponding association
            # between the device and the device feature model
            dfm_list = self.__session.query(
                                DeviceFeatureModel
                            ).filter_by(device_type_id=device.device_type_id
                            ).all()
            for dfm in dfm_list:
                df = DeviceFeature(device_id=device.id, device_feature_model_id=dfm.id)
                self.__session.add(df)
            self.__session.commit()
        except Exception as sql_exception:
            self.__raise_dbhelper_exception("SQL exception (commit) : %s" % sql_exception, True)
        return device

    def update_device(self, d_id, d_name=None, d_address=None, d_usage_id=None, d_description=None, d_reference=None):
        """Update a device item

        If a param is None, then the old value will be kept

        @param d_id : Device id
        @param d_name : device name (optional)
        @param d_address : Item address (ex : 'A3' for x10/plcbus, '111.111111111' for 1wire) (optional)
        @param d_description : Extended item description (optional)
        @param d_usage : Item usage id (optional)
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
            # only do the check if we update the device address
            if device.address != ucode(d_address) and self.__session.query(Device).filter(Device.address==d_address).filter(Device.device_type_id==device.device_type_id).count() != 0:
                self.__raise_dbhelper_exception("Couldn't update device, same device with adress %s and type %s already exists" % (d_address,device.device_type_id))
            device.address = ucode(d_address)
        if d_description is not None:
            if d_description == '': d_description = None
            device.description = ucode(d_description)
        if d_reference is not None:
            if d_reference == '': d_reference = None
            device.reference = ucode(d_reference)
        if d_usage_id is not None:
            if not self.__session.query(DeviceUsage).filter_by(id=d_usage_id).first():
                self.__raise_dbhelper_exception("Couldn't find device usage id %s. It does not exist" % d_usage_id)
            device.device_usage_id = d_usage_id
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
        result = self.__session.execute(
            t_stats.delete().where(t_stats.c.device_id == d_id)
        )
        
        self.__session.delete(device)
        try:
            self.__session.commit()
        except Exception as sql_exception:
            self.__raise_dbhelper_exception("SQL exception (commit) : %s" % sql_exception, True)
        return device

####
# Device stats
####
    def lis_device_stats_distinct_key(self, ds_device_id):
        filters = {}
        filters['device_id'] = ds_device_id
        return self.__session.query(
                            DeviceStats
                        ).filter_by(**filters
                        ).distinct()

    def list_device_stats(self, ds_device_id=None,ds_skey=None,ds_number=None):
        """Return a list of all stats for a device

        @param ds_device_id : the device id
        @param ds_key : statistic key
        @return a list of DeviceStats objects

        """
        
        filters = {}
        if ds_device_id:
            filters['device_id'] = ds_device_id
        if ds_skey:
            filters['skey'] = ucode(ds_skey)
        
        if ds_number:
            return self.__session.query(
                            DeviceStats
                        ).filter_by(**filters
                        ).limit(ds_number
                        ).all()
        else:
            return self.__session.query(
                            DeviceStats
                        ).filter_by(**filters
                        ).all()


    def list_last_n_stats_of_device(self, ds_device_id=None,ds_skey=None,ds_number=None):
        """Get the N latest statistics of a device for a given key

        @param ds_device_id : the device id
        @param ds_key : statistic key
        @param ds_number : the number of statistics we want to retreive
        @return a list of DeviceStats objects (older records first)

        """
        filters = {}
        if ds_device_id:
            filters['device_id'] = ds_device_id
        if ds_skey:
            filters['skey'] = ucode(ds_skey)

        list_s = self.__session.query(
                            DeviceStats
                        ).filter_by(**filters
                        ).order_by(sqlalchemy.desc(DeviceStats.date)
                        ).limit(ds_number
                        ).all()
        list_s.reverse()
        return list_s
    
    def list_stats_of_device_between_by_key(self, ds_device_id=None, ds_skey=None, start_date_ts=None, end_date_ts=None):
        """Get statistics of a device between two dates for a given key

        @param ds_device_id : the device id
        @param ds_key : statistic key
        @param start_date_ts : datetime start, optional (timestamp)
        @param end_date_ts : datetime end, optional (timestamp)
        @return a list of DeviceStats objects (older records first)

        """
        if start_date_ts and end_date_ts:
            if end_date_ts < start_date_ts:
                self.__raise_dbhelper_exception("'end_date' can't be prior to 'start_date'")
        
        query = self.__session.query(DeviceStats)
        if ds_device_id:
            query = query.filter_by(device_id=ds_device_id)
        if ds_skey:
            query = query.filter_by(skey= ucode(ds_skey))
        
        if start_date_ts:
            query = query.filter("date >= '" + _datetime_string_from_tstamp(start_date_ts)+"'")
        if end_date_ts:
            query = query.filter("date <= '" + _datetime_string_from_tstamp(end_date_ts) + "'")
            
        list_s = query.order_by(sqlalchemy.asc(DeviceStats.date)).all()
        return list_s

    def get_last_stat_of_device(self, ds_device_id=None,ds_skey=None):
        """Get the latest statistic of a device for a given key

        @param ds_device_id : the device id
        @param ds_skey : statistic key
        @return a DeviceStats object

        """
        filters = {}
        if ds_device_id:
            filters['device_id'] = ds_device_id
        if ds_skey:
            filters['skey'] = ucode(ds_skey)

        return self.__session.query(
                        DeviceStats
                    ).filter_by(**filters
                    ).order_by(sqlalchemy.desc(DeviceStats.date)
                    ).first()

    def filter_stats_of_device_by_key(self, ds_device_id, ds_key,  start_date_ts, end_date_ts, step_used, function_used):
        """Filter statistic values within a period for a given step (minute, hour, day, week, month, year). It then
        applies a function (min, max, avg) for the values within the step.

        @param ds_key : statistic key
        @param ds_device_id : device_id
        @param start_date_ts : date representing the begin of the period (timestamp)
        @param end_date_ts : date reprensenting the end of the period (timestamp)
        @param step_used : minute, hour, day, week, month, year
        @param function_used : min, max, avg
        @return a list of tuples (date, computed value)

        """
        if not start_date_ts:
            self.__raise_dbhelper_exception("You have to provide a start date")
        if end_date_ts:
            if start_date_ts > end_date_ts:
                self.__raise_dbhelper_exception("'end_date' can't be prior to 'start_date'")
        else:
            end_date_ts = time.mktime(datetime.datetime.now().timetuple())

        if function_used is None or function_used.lower() not in ('min', 'max', 'avg'):
            self.__raise_dbhelper_exception("'function_used' parameter should be one of : min, max, avg")
        if step_used is None or step_used.lower() not in ('minute', 'hour', 'day', 'week', 'month', 'year'):
            self.__raise_dbhelper_exception("'period' parameter should be one of : minute, hour, day, week, month, year")
        function = {
            'min': func.min(DeviceStats._DeviceStats__value_num),
            'max': func.max(DeviceStats._DeviceStats__value_num),
            'avg': func.avg(DeviceStats._DeviceStats__value_num),
        }
        sql_query = {
            'minute' : {
                # Query for mysql
                # func.week(DeviceStats.date, 3) is equivalent to python's isocalendar()[2] method
                'mysql': self.__session.query(
                            func.year(DeviceStats.date), func.month(DeviceStats.date),
                            func.week(DeviceStats.date, 3), func.day(DeviceStats.date),
                            func.hour(DeviceStats.date), func.minute(DeviceStats.date),
                            function[function_used]
                        ).group_by(
                            func.year(DeviceStats.date), func.month(DeviceStats.date),
                            func.day(DeviceStats.date), func.hour(DeviceStats.date),
                            func.minute(DeviceStats.date)
                        ),
                 'postgresql': self.__session.query(
                            extract('year', DeviceStats.date).label('year_c'), extract('month', DeviceStats.date),
                            extract('week', DeviceStats.date), extract('day', DeviceStats.date),
                            extract('hour', DeviceStats.date), extract('minute', DeviceStats.date),
                            function[function_used]
                        ).group_by(
                            extract('year', DeviceStats.date), extract('month', DeviceStats.date),
                            extract('week', DeviceStats.date), extract('day', DeviceStats.date),
                            extract('hour', DeviceStats.date), extract('minute', DeviceStats.date)
                        ).order_by(
                            sqlalchemy.asc('year_c')
                        )
            },
            'hour' : {
                'mysql': self.__session.query(
                            func.year(DeviceStats.date), func.month(DeviceStats.date),
                            func.week(DeviceStats.date, 3), func.day(DeviceStats.date),
                            func.hour(DeviceStats.date), function[function_used]
                        ).group_by(
                            func.year(DeviceStats.date), func.month(DeviceStats.date),
                            func.day(DeviceStats.date), func.hour(DeviceStats.date)
                        ),
                'postgresql': self.__session.query(
                            extract('year', DeviceStats.date).label('year_c'), extract('month', DeviceStats.date),
                            extract('week', DeviceStats.date), extract('day', DeviceStats.date),
                            extract('hour', DeviceStats.date),
                            function[function_used]
                        ).group_by(
                            extract('year', DeviceStats.date), extract('month', DeviceStats.date),
                            extract('week', DeviceStats.date), extract('day', DeviceStats.date),
                            extract('hour', DeviceStats.date)
                        ).order_by(
                            sqlalchemy.asc('year_c')
                        )
            },
            'day' : {
                'mysql': self.__session.query(
                            func.year(DeviceStats.date), func.month(DeviceStats.date),
                            func.week(DeviceStats.date, 3), func.day(DeviceStats.date),
                                      function[function_used]
                        ).group_by(
                            func.year(DeviceStats.date), func.month(DeviceStats.date),
                            func.day(DeviceStats.date)
                        ),
                'postgresql': self.__session.query(
                            extract('year', DeviceStats.date).label('year_c'), extract('month', DeviceStats.date),
                            extract('week', DeviceStats.date), extract('day', DeviceStats.date),
                            function[function_used]
                        ).group_by(
                            extract('year', DeviceStats.date), extract('month', DeviceStats.date),
                            extract('week', DeviceStats.date), extract('day', DeviceStats.date)
                        ).order_by(
                            sqlalchemy.asc('year_c')
                        )
            },
            'week' : {
                'mysql': self.__session.query(
                            func.year(DeviceStats.date), func.week(DeviceStats.date, 1), function[function_used]
                        ).group_by(
                            func.year(DeviceStats.date), func.week(DeviceStats.date, 1)
                        ),
                'postgresql': self.__session.query(
                            extract('year', DeviceStats.date).label('year_c'), extract('week', DeviceStats.date),
                            function[function_used]
                        ).group_by(
                            extract('year', DeviceStats.date).label('year_c'), extract('week', DeviceStats.date)
                        ).order_by(
                            sqlalchemy.asc('year_c')
                        )
            },
            'month' : {
                'mysql': self.__session.query(
                            func.year(DeviceStats.date), func.month(DeviceStats.date),
                            function[function_used]
                        ).group_by(
                            func.year(DeviceStats.date),
                            func.month(DeviceStats.date)
                        ),
                'postgresql': self.__session.query(
                            extract('year', DeviceStats.date).label('year_c'), extract('month', DeviceStats.date),
                            function[function_used]
                        ).group_by(
                            extract('year', DeviceStats.date), extract('month', DeviceStats.date)
                        ).order_by(
                            sqlalchemy.asc('year_c')
                        )
            },
            'year' : {
                'mysql': self.__session.query(
                            func.year(DeviceStats.date), function[function_used]
                        ).group_by(
                            func.year(DeviceStats.date)
                        ),
                'postgresql': self.__session.query(
                            extract('year', DeviceStats.date).label('year_c'), function[function_used]
                        ).group_by(
                            extract('year', DeviceStats.date)
                        ).order_by(
                            sqlalchemy.asc('year_c')
                        )
            },
            'global' : self.__session.query(
                            function['min'], function['max'], function['avg']
                        )
        }

        if self.get_db_type() in ('mysql', 'postgresql'):
            cond_min = "date >= '" + _datetime_string_from_tstamp(start_date_ts) + "'"
            cond_max = "date < '" + _datetime_string_from_tstamp(end_date_ts) + "'"
            query = sql_query[step_used][self.get_db_type()]
            query = query.filter_by(skey=ucode(ds_key)
                        ).filter_by(device_id=ds_device_id
                        ).filter(cond_min
                        ).filter(cond_max)
            results_global = sql_query['global'].filter_by(skey=ucode(ds_key)
                                               ).filter_by(device_id=ds_device_id
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

    def device_has_stats(self, ds_device_id=None,ds_skey=None):
        """Check if the device has stats that were recorded

        @param ds_device_id : the device id
        @param ds_key : statistic key
        @return True or False

        """
        return len(self.list_device_stats(ds_device_id,ds_skey,1)) > 0

    def _get_duplicated_devicestats_id(self, device_id, key, value):
        """Check if the data is duplicated with older values
        
        @param device_id : device id
        @param key : stat key
        @value : stat value
        
        """
        my_db = DbHelper()
        
        db_round_filter = None
        self.log.debug("before read config")

        if self.__db_config.has_key('db_round_filter'):
            db_round = self.__db_config['db_round_filter']
            db_round_filter = json.loads(db_round)
        
        self.log.debug("after read")
        last_values = my_db.list_last_n_stats_of_device(device_id, key, ds_number=2)
        if last_values and len(last_values)>=2:
            # TODO, remove this, just for testing in developpement (actually in domogik.cfg)
            # Ex: db_round_filter = {"12" : { "total_space" : 1048576, "free_space" : 1048576, "percent_used" : 0.5, "used_space": 1048576 },"13" : { "hchp" : 500, "hchc" : 500, "papp" : 200 }}
            self.log.debug("key=%s : value=%s / val0=%s / val1=%s (%s)" % (key,value, last_values[0].value, last_values[1].value,id))
            if db_round_filter and str(last_values[1].device.id) in db_round_filter and key in db_round_filter[str(last_values[1].device.id)]:
                    round_value = db_round_filter[str(last_values[1].device.id)][last_values[1].skey]
                    rvalue = int(float(value) / round_value) * round_value
                    val0 = int(float(last_values[0].value) / round_value) * round_value
                    val1 = int(float(last_values[1].value) / round_value) * round_value
                    self.log.debug("rvalue=%s" % rvalue)
                    self.log.debug("value=%s(%s) / val0=%s / val1=%s" % (rvalue, value, val0, val1))
            else:
                rvalue = value
                val0 = last_values[0].value
                val1 = last_values[1].value
            
            if val0 == val1 and val0 == rvalue:
                self.log.debug("REMOVE %s for %s(%s)" % (last_values[1].id, last_values[1].device.id,key))
                return last_values[1].id
        
        return None


    def add_device_stat(self, ds_timestamp, ds_key, ds_value, ds_device_id, hist_size=0):
        """Add a device stat record

        @param ds_key : key for the stat
        @param ds_timestamp : when the stat was gathered
        @param ds_value : stat value
        @param ds_device_id : device id
        @param hist_size : keep only the last hist_size records after having inserted the item (default is 0 which
        means to keep all values)
        @return the new DeviceStats object

        """
        # Make sure previously modified objects outer of this method won't be commited
        self.__session.expire_all()

        # Remove intermediate data
        duplicated_id = self._get_duplicated_devicestats_id(ds_device_id,ds_key,ds_value)
        if duplicated_id:
            old_stat = self.__session.query(DeviceStats).filter_by(id=duplicated_id).first()
            if old_stat:
                self.__session.delete(old_stat)
            else:
                # FIXME : shouldn't occur (just for debug purposes related to bug #1503)
                self.log.error("Can't delete stats for device id '%s' : it doesn't exist" % duplicated_id) 

        if not self.__session.query(Device).filter_by(id=ds_device_id).first():
            self.__raise_dbhelper_exception("Couldn't add device stat with device id %s. It does not exist" % ds_device_id)
        device_stat = DeviceStats(date=datetime.datetime.fromtimestamp(ds_timestamp), timestamp=ds_timestamp,
                                  skey=ds_key, value=ds_value, device_id=ds_device_id)
        self.__session.add(device_stat)
        try:
            self.__session.commit()
        except Exception as sql_exception:
            self.__raise_dbhelper_exception("SQL exception (commit) : %s" % sql_exception, True)
        # Eventually remove old stats
        if hist_size > 0:
            stats_list = self.__session.query(
                                    DeviceStats
                                ).filter_by(device_id=ds_device_id
                                ).filter_by(skey=ucode(ds_key)
                                ).order_by(sqlalchemy.desc(DeviceStats.date))[:hist_size]
            last_date_to_keep = stats_list[len(stats_list)-1].date
            stats_list = self.__session.query(
                                    DeviceStats
                                ).filter_by(device_id=ds_device_id
                                ).filter_by(skey=ucode(ds_key)
                                ).filter("date < '" + str(last_date_to_keep) + "'"
                                ).all()
            for stat in stats_list:
                self.__session.delete(stat)
            try:
                self.__session.commit()
            except Exception as sql_exception:
                self.__raise_dbhelper_exception("SQL exception (commit) : %s" % sql_exception, True)

        return device_stat

    def del_device_stats(self, ds_device_id, ds_key=None):
        """Delete a stat record for a given key and device

        @param ds_device_id : device id
        @param ds_key : stat key, optional
        @return list of deleted DeviceStat objects

        """
        # Make sure previously modified objects outer of this method won't be commited
        self.__session.expire_all()
        query = self.__session.query(DeviceStats).filter_by(device_id=ds_device_id)
        if ds_key:
            query = query.filter_by(skey=ucode(ds_key))
        device_stats_l = query.all()
        for ds in device_stats_l:
            self.__session.delete(ds)
        try:
            self.__session.commit()
        except Exception as sql_exception:
            self.__raise_dbhelper_exception("SQL exception (commit) : %s" % sql_exception, True)
        return device_stats_l


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
        default_person_fname = "Admin"
        default_person_lname = "Admin"
        default_user_account_login = "admin"
        if self.__session.query(UserAccount).count() > 0:
            return None
        person = self.add_person(p_first_name=default_person_fname, p_last_name=default_person_lname, 
                                 p_birthdate=datetime.date(1900, 01, 01))
        return self.add_user_account(a_login=default_user_account_login, a_password='123', a_person_id=person.id, 
                                     a_is_admin=True)

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
        self.__session.expire_all()
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
        self.__session.expire_all()
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

    def __raise_dbhelper_exception(self, error_msg, with_rollback=False):
        """Raise a DbHelperException and log it

        @param error_msg : error message
        @param with_rollback : True if a rollback should be done (default is set to False)

        """
        self.log.error(error_msg)
        if with_rollback:
            self.__session.rollback()
        raise DbHelperException(error_msg)

