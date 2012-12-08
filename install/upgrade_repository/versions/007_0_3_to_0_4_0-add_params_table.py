from sqlalchemy import *
from migrate import *
from domogik.common.sql_schema import XplStat, XplStatParam, XplCommand, XplCommandParam, DeviceFeatureModel, Device, Command, CommandParam
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
    if database_utils.table_exists(migrate_engine, DeviceFeatureModel.__tablename__):
        table = DeviceFeatureModel.__table__
        table.drop(bind=migrate_engine)
    if database_utils.table_exists(migrate_engine, DeviceFeature.__tablename__):
        table = DeviceFeature.__table__
        table.drop(bind=migrate_engine)

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
