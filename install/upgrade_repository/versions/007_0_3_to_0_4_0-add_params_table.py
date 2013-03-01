from sqlalchemy import *
from migrate import *
from domogik.common.sql_schema import XplStat, XplStatParam, XplCommand, XplCommandParam, Device, Command, CommandParam, Sensor, SensorHistory, DeviceType, Plugin
from domogik.common import database_utils

def upgrade(migrate_engine):
    # bind the engine
    meta = MetaData(bind=migrate_engine)

    # create the new table
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
        dev= Table(Device.__tablename__, meta, autoload=True)
        dev.c.address.alter(nullable=True)
        dev.c.device_type_id.alter(nullable=True)
    # delete feature and featureModels
    if database_utils.table_exists(migrate_engine, "core_device_feature_association"):
        migrate_engine.execute("DROP table core_device_feature_association")
    if database_utils.table_exists(migrate_engine, "core_device_feature"):
        migrate_engine.execute("DROP table core_device_feature")
    if database_utils.table_exists(migrate_engine, "core_device_feature_model"):
        migrate_engine.execute("DROP table core_device_feature_model")
    # technology to plugin renaming
    #0- delete foreign key between device and device_type
    dev = Table(Device.__tablename__, meta, autoload=True)
    devtype = Table(DeviceType.__tablename__, meta, autoload=True)
    cons = ForeignKeyConstraint([dev.c.device_type_id], [devtype.c.id], name='core_device_ibfk_2')
    cons.drop()
    cons = None
    dev = None
    devtype = None
    #1- delete device_type
    if database_utils.table_exists(migrate_engine, "core_device_type"):
        migrate_engine.execute("DROP table core_device_type")
    #2- delete technology
    if database_utils.table_exists(migrate_engine, "core_device_technology"):
        migrate_engine.execute("DROP table core_device_technology")
    #3- create device_type
    if not database_utils.table_exists(migrate_engine, Plugin.__tablename__):
        table = Plugin.__table__
        table.create(bind=migrate_engine)
    #5- create plugin
    if not database_utils.table_exists(migrate_engine, DeviceType.__tablename__):
        table = DeviceType.__table__
        table.create(bind=migrate_engine)
    #6- re-add the foreign key
    dev = Table(Device.__tablename__, meta, autoload=True)
    devtype = Table(DeviceType.__tablename__, meta, autoload=True)
    cons = ForeignKeyConstraint([dev.c.device_type_id], [devtype.c.id], name='core_device_ibfk_2')
    cons.create()

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
