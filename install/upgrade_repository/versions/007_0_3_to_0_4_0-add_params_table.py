from sqlalchemy import *
from migrate import *
from domogik.common.sql_schema import XplStat, XplStatParam, XplCommand, XplCommandParam, Device, Command, CommandParam, Sensor, SensorHistory
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
    # delete feature and featureModels
    if database_utils.table_exists(migrate_engine, "core_device_feature_association"):
        migrate_engine.execute("DROP table core_device_feature_association")
    if database_utils.table_exists(migrate_engine, "core_device_feature"):
        migrate_engine.execute("DROP table core_device_feature")
    if database_utils.table_exists(migrate_engine, "core_device_feature_model"):
        migrate_engine.execute("DROP table core_device_feature_model")
    # technology removal
    # 0- delete foreign key between device and device_type
    # 1- set device_type to null
    # 2- empty device_type
    # 3- empty technology
    # 4- rename table
    # 5- rename field in device_type
    # 6- re-add the foreign key


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
