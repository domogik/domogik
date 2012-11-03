from sqlalchemy import *
from migrate import *
from domogik.common.sql_schema import XplStat, XplStatParam, XplCommand, XplCommandParam


def upgrade(migrate_engine):
    # bind the engine
    meta = MetaData(bind=migrate_engine)

    # create the new table
    table = XplStat.__table__
    table.create(bind=migrate_engine)
    table = XplStatParam.__table__
    table.create(bind=migrate_engine)
    table = XplCommand.__table__
    table.create(bind=migrate_engine)
    table = XplCommandParam.__table__
    table.create(bind=migrate_engine)

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


