from sqlalchemy import Table, MetaData, String, Column

def upgrade(migrate_engine):
    meta = MetaData(bind=migrate_engine)

    #939
    core_device = Table('core_device', meta, autoload=True)
    core_device.c.address.alter(type=String(255))

    #1064
    core_plugin_config = Table('core_plugin_config', meta, autoload=True)
    core_plugin_config.c.name.alter(name='id')

    #1110
    core_device_type = Table('core_device_type', meta, autoload=True)
    core_device_type.c.name.alter(type=String(80))
    

def downgrade(migrate_engine):
    meta = MetaData(bind=migrate_engine)

    #939
    core_device = Table('core_device', meta, autoload=True)
    core_device.c.address.alter(type=String(30))

    #1064
    core_plugin_config = Table('core_plugin_config', meta, autoload=True)
    core_plugin_config.c.id.alter(name='name')

    #1110
    core_device_type = Table('core_device_type', meta, autoload=True)
    core_device_type.c.name.alter(type=String(30))
