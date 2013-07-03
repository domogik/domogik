from sqlalchemy import *
from sqlalchemy.orm import sessionmaker
from migrate import *
from domogik.common.sql_schema import XplStat, XplStatParam, XplCommand, XplCommandParam, Device, Command, CommandParam, Sensor, SensorHistory, PluginConfig
from domogik.common import database_utils

def upgrade(migrate_engine):
    # bind the engine
    meta = MetaData(bind=migrate_engine)

    #reate the new table
    if not database_utils.table_exists(migrate_engine, Command.__tablename__):
        table = Command.__table__
        table.create(bind=migrate_engine)
    if not database_utils.table_exists(migrate_engine, CommandParam.__tablename__):
        table = CommandParam.__table__
        table.create(bind=migrate_engine)
    if not database_utils.table_exists(migrate_engine, Sensor.__tablename__):
        table = Sensor.__table__
        table.create(bind=migrate_engine)
    if not database_utils.table_exists(migrate_engine, SensorHistory.__tablename__):
        table = SensorHistory.__table__
        table.create(bind=migrate_engine)
    if not database_utils.table_exists(migrate_engine, XplStat.__tablename__):
        table = XplStat.__table__
        table.create(bind=migrate_engine)
    if not database_utils.table_exists(migrate_engine, XplStatParam.__tablename__):
        table = XplStatParam.__table__
        table.create(bind=migrate_engine)
    if not database_utils.table_exists(migrate_engine, XplCommand.__tablename__):
        table = XplCommand.__table__
        table.create(bind=migrate_engine)
    if not database_utils.table_exists(migrate_engine, XplCommandParam.__tablename__):
        table = XplCommandParam.__table__
        table.create(bind=migrate_engine)
    # device address make nullable
    if database_utils.column_exists(migrate_engine, Device.__tablename__, 'address'):
        dev = Table(Device.__tablename__, meta, autoload=True)
        dev.c.address.alter(nullable=True)
    # delete some foreign keys
    dev = Table(Device.__tablename__, meta, autoload=True)
    devu = Table('core_device_usage', meta, autoload=True)
    devt = Table('core_device_type', meta, autoload=True)
    devtt = Table('core_device_technology', meta, autoload=True)
    cons = ForeignKeyConstraint([dev.c.device_usage_id], [devu.c.id], name='core_device_ibfk_1').drop()
    cons = ForeignKeyConstraint([dev.c.device_type_id], [devt.c.id], name='core_device_ibfk_2').drop()
    cons = ForeignKeyConstraint([devt.c.device_technology_id], [devtt.c.id], name='core_device_type_ibfk_1').drop()
    dev.c.device_usage_id.drop()
    dev.c.device_type_id.drop()
    # drop device_usage in device table and the table itself
    #if database_utils.table_exists(migrate_engine, "core_device_feature_association"):
    #    devt = Table('core_device_feature_association', meta, autoload=True)
    #    devt.drop()
    if database_utils.table_exists(migrate_engine, "core_device_feature"):
        tab = Table('core_device_feature', meta, autoload=True)
        tab.drop()
        tab = None
    if database_utils.table_exists(migrate_engine, "core_device_feature_model"):
        tab = Table('core_device_feature_model', meta, autoload=True)
        tab.drop()
        tab = None
    if database_utils.table_exists(migrate_engine, "core_device_technology"):
        devtt.drop()
        devtt = None
    if database_utils.table_exists(migrate_engine, "core_device_type"):
        devt.drop()
        devt = None
    if database_utils.table_exists(migrate_engine, "core_device_usage"):
        devu.drop()
        devu = None
    dev = None
    # pluginConfig => key to length 255
    # pluginConfig => value to text
    pluginConfig = Table(PluginConfig.__tablename__, meta, autoload=True)
    pluginConfig.c.key.alter(type=Unicode(255))
    pluginConfig.c.value.alter(type=UnicodeText())
 
def downgrade(migrate_engine):
    # bind the engine
    meta = MetaData(bind=migrate_engine)

    # drop the page table
    table = XplStat.__table__
    table.drop()
    table = XplStatParam.__table__
    table.drop()
    table = XplCommand.__table__
    table.drop()
    table = XplCommandParam.__table__
    table.drop()
