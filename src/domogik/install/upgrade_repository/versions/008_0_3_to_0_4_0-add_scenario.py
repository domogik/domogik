from sqlalchemy import *
from sqlalchemy.orm import sessionmaker
from migrate import *
from domogik.common.sql_schema import Scenario
from domogik.common import database_utils

def upgrade(migrate_engine):
    # bind the engine
    meta = MetaData(bind=migrate_engine)

    #reate the new table
    if not database_utils.table_exists(migrate_engine, Scenario.__tablename__):
        table = Scenario.__table__
        table.create(bind=migrate_engine)
 
def downgrade(migrate_engine):
    # bind the engine
    meta = MetaData(bind=migrate_engine)

    # drop the page table
    table = Scenario.__table__
    table.drop()
