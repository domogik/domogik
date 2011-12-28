from sqlalchemy import MetaData, Table
from domogik.common.sql_schema import DeviceUsage

def upgrade(migrate_engine):
    meta = MetaData(bind=migrate_engine)
    #1078
    core_device_usage = Table(DeviceUsage.__tablename__, meta, autoload=True)
    insert = core_device_usage.insert()
    insert.execute(id='water_tank', name='Water Tank', description='Water tank usage', 
                   default_options='{ &quot;actuator&quot;: { &quot;binary&quot;: {&quot;state0&quot;:&quot;Off&quot;, &quot;state1&quot;:&quot;On&quot;}, &quot;range&quot;: {&quot;step&quot;:10, &quot;unit&quot;:&quot;%&quot;}, &quot;trigger&quot;: {}, &quot;number&quot;: {} }, &quot;sensor&quot;: {&quot;boolean&quot;: {}, &quot;number&quot;: {}, &quot;string&quot;: {} } }')
    insert.execute(id='christmas_tree', name='Christmas Tree', description='Happy Christmas!!',
                   default_options='{&quot;actuator&quot;: { &quot;binary&quot;: {}, &quot;range&quot;: {}, &quot;trigger&quot;: {}, &quot;number&quot;: {} }, &quot;sensor&quot;: {&quot;boolean&quot;: {}, &quot;number&quot;: {}, &quot;string&quot;: {} }}')
    insert.execute(id='portal', name='Portal', description='Portal',
                   default_options='{ &quot;actuator&quot;: { &quot;binary&quot;: {&quot;state0&quot;:&quot;Closed&quot;, &quot;state1&quot;:&quot;Open&quot;}, &quot;range&quot;: {&quot;step&quot;:10, &quot;unit&quot;:&quot;%&quot;}, &quot;trigger&quot;: {}, &quot;number&quot;: {} }, &quot;sensor&quot;: {&quot;boolean&quot;: {}, &quot;number&quot;: {}, &quot;string&quot;: {} } }')
    insert.execute(id='security_camera', name='Security camera', description='Security camera',
                   default_options='{&quot;actuator&quot;: { &quot;binary&quot;: {}, &quot;range&quot;: {}, &quot;trigger&quot;: {}, &quot;number&quot;: {} }, &quot;sensor&quot;: {&quot;boolean&quot;: {}, &quot;number&quot;: {}, &quot;string&quot;: {} }}')

def downgrade(migrate_engine):
    meta = MetaData(bind=migrate_engine)
    #1078
    core_device_usage = Table(DeviceUsage.__tablename__, meta, autoload=True)
    core_device_usage.delete(whereclause="id='water_tank'").execute()
    core_device_usage.delete(whereclause="id='christmas_tree'").execute()
    core_device_usage.delete(whereclause="id='portal'").execute()
    core_device_usage.delete(whereclause="id='security_camera'").execute()
