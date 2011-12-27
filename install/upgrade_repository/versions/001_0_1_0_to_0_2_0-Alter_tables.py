from sqlalchemy import Table, MetaData, String, Column, Index
from domogik.common.sql_schema import Device, PluginConfig, DeviceType, DeviceStats

def upgrade(migrate_engine):
    meta = MetaData(bind=migrate_engine)

    #939
    core_device = Table(Device.__tablename__, meta, autoload=True)
    core_device.c.address.alter(type=String(255))

    #1064
    core_plugin_config = Table(PluginConfig.__tablename__, meta, autoload=True)
    core_plugin_config.c.name.alter(name='id')

    #1110
    core_device_type = Table(DeviceType.__tablename__, meta, autoload=True)
    core_device_type.c.name.alter(type=String(80))
    
    #1061
    core_device_stats = Table(DeviceStats.__tablename__, meta, autoload=True)
    Index('ix_core_device_stats_skey', core_device_stats.c.skey).create()

def downgrade(migrate_engine):
    meta = MetaData(bind=migrate_engine)

    #939
    core_device = Table(Device.__tablename__, meta, autoload=True)
    core_device.c.address.alter(type=String(30))

    #1064
    core_plugin_config = Table(PluginConfig.__tablename__, meta, autoload=True)
    core_plugin_config.c.id.alter(name='name')

    #1110
    core_device_type = Table(DeviceType.__tablename__, meta, autoload=True)
    core_device_type.c.name.alter(type=String(30))

    #1061
    core_device_stats = Table(DeviceStats.__tablename__, meta, autoload=True)
    Index('ix_core_device_stats_skey', core_device_stats.c.skey).drop()
