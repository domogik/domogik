from sqlalchemy import *
from migrate import *
from domogik.common.sql_schema import XplStat, XplStatParam, XplCommand, XplCommandParam, DeviceFeatureModel
from domogik.common import database_utils

def upgrade(migrate_engine):
    # bind the engine
    meta = MetaData(bind=migrate_engine)

    # create the new table
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

    table = Table(DeviceFeatureModel.__tablename__, meta, autoload=True)
    if not database_utils.column_exists(migrate_engine, DeviceFeatureModel.__tablename__, 'xpl_command'):
        c = Column('xpl_command', Unicode(255), nullable=True)
        c.create(table)
    if not database_utils.column_exists(migrate_engine, DeviceFeatureModel.__tablename__, 'value_field'):
        c = Column('value_field', Unicode(32), nullable=True)
        c.create(table)
    if not database_utils.column_exists(migrate_engine, DeviceFeatureModel.__tablename__, 'values'):
        c = Column('values', Unicode(255), nullable=True)
        c.create(table)
    if not database_utils.column_exists(migrate_engine, DeviceFeatureModel.__tablename__, 'unit'):
	c = Column('unit', Unicode(32), nullable=True)
        c.create(table)

    if database_utils.column_exists(migrate_engine, DeviceFeatureModel.__tablename__, 'parameters'):
        c = Column('parameters', UnicodeText())
        c.drop(table)
    if database_utils.column_exists(migrate_engine, DeviceFeatureModel.__tablename__, 'return_confirmation'):
        c = Column('return_confimation', Boolean, nullable=False)
        c.drop(table) 

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
