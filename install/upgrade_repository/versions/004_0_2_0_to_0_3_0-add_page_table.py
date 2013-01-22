from sqlalchemy import *
from migrate import *
from domogik.common import database_utils

def upgrade(migrate_engine):
    # core_device_config
    if database_utils.table_exists(migrate_engine, "core_room"):
        migrate_engine.execute("DROP table core_room")
    # core_system_info
    if database_utils.table_exists(migrate_engine, "core_area"):
        migrate_engine.execute("DROP table core_area")
    return

def downgrade(migrate_engine):
    return
