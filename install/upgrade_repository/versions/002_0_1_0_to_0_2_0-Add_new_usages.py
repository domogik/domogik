from sqlalchemy import MetaData, Table
from domogik.common.sql_schema import DeviceUsage

def upgrade(migrate_engine):
    meta = MetaData(bind=migrate_engine)
    #1078
    core_device_usage = Table('core_device_usage', meta, autoload=True)
    insert = core_device_usage.insert()
    insert.execute(id='water_tank', name='Water Tank', description='Water tank usage', 
                   default_options='{ "actuator": { "binary": {"state0":"Off", "state1":"On"}, "range": {"step":10, "unit":"%"}, "trigger": {}, "number": {} }, "sensor": {"boolean": {}, "number": {}, "string": {} } }')
    insert.execute(id='christmas_tree', name='Christmas Tree', description='Happy Christmas!!',
                   default_options='{"actuator": { "binary": {}, "range": {}, "trigger": {}, "number": {} }, "sensor": {"boolean": {}, "number": {}, "string": {} }}')
    insert.execute(id='portal', name='Portal', description='Portal',
                   default_options='{ "actuator": { "binary": {"state0":"Closed", "state1":"Open"}, "range": {"step":10, "unit":"%"}, "trigger": {}, "number": {} }, "sensor": {"boolean": {}, "number": {}, "string": {} } }')
    insert.execute(id='security_camera', name='Security camera', description='Security camera',
                   default_options='{"actuator": { "binary": {}, "range": {}, "trigger": {}, "number": {} }, "sensor": {"boolean": {}, "number": {}, "string": {} }}')

def downgrade(migrate_engine):
    meta = MetaData(bind=migrate_engine)
    #1078
    core_device_usage = Table('core_device_usage', meta, autoload=True)
    core_device_usage.delete(whereclause="id='water_tank'").execute()
    core_device_usage.delete(whereclause="id='christmas_tree'").execute()
    core_device_usage.delete(whereclause="id='portal'").execute()
    core_device_usage.delete(whereclause="id='security_camera'").execute()
